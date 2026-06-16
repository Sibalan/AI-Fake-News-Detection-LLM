import requests
import json
import re
import logging
import os
import subprocess
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus
from typing import Dict, Any, Optional, List
import groq_client

try:
    import feedparser

    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
PRIMARY_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
FAST_MODEL = "tinyllama:latest"

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

VISION_MODEL_BLACKLIST = set()


def _is_vision_model(model_name: str) -> bool:
    vision_keywords = [
        "llava",
        "bakllava",
        "cogvlm",
        "moondream",
        "minicpm-v",
        "phi3-v",
        "vision",
    ]
    name_lower = model_name.lower()
    for kw in vision_keywords:
        if kw in name_lower:
            return True
    return False


def _try_inference(
    model: str, prompt: str, max_tokens: int, timeout: int
) -> Optional[str]:
    if model in VISION_MODEL_BLACKLIST:
        logger.debug(f"{model} is blacklisted (vision model) — skipping")
        return None
    if _is_vision_model(model):
        logger.debug(f"{model} appears to be a vision model — skipping")
        return None
    for fmt in ("chat", "generate"):
        try:
            if fmt == "chat":
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.0, "max_tokens": max_tokens},
                }
            else:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "max_tokens": max_tokens},
                }
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/{fmt}",
                json=payload,
                timeout=timeout,
            )
            if resp.status_code == 200:
                raw = resp.json()
                content = (
                    raw.get("message", {}).get("content", "")
                    if fmt == "chat"
                    else raw.get("response", "")
                )
                if content.strip():
                    return content
            err_body = resp.text[:300].lower()
            if "image.png" in err_body or "does not support image" in err_body:
                logger.debug(f"{model} vision error on {fmt} — blacklisting {model}")
                VISION_MODEL_BLACKLIST.add(model)
                break
        except requests.exceptions.Timeout:
            logger.debug(f"{model} {fmt} timed out ({timeout}s)")
        except Exception as e:
            logger.debug(f"{model} {fmt} error: {e}")
    return None


def _call_ollama(prompt: str, max_tokens: int = 400) -> Optional[str]:
    try:
        alive = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if alive.status_code != 200:
            return None
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        logger.warning("Ollama health check timed out - skipping LLM")
        return None
    except Exception:
        return None

    result = _try_inference(PRIMARY_MODEL, prompt, max_tokens, 30)
    if result:
        return result

    result = _try_inference(FAST_MODEL, prompt, max_tokens, 20)
    if result:
        return result

    return None


def _restart_ollama():
    try:
        logger.info("Attempting to restart hung Ollama server...")
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/f", "/im", "ollama.exe"], capture_output=True, timeout=3
            )
            time.sleep(1)
            subprocess.Popen(
                ["ollama", "serve"], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            subprocess.run(["killall", "-9", "ollama"], capture_output=True, timeout=3)
            time.sleep(1)
            subprocess.Popen(["ollama", "serve"], start_new_session=True)
        time.sleep(2)
        logger.info("Ollama restart initiated")
        return True
    except subprocess.TimeoutExpired:
        logger.warning("Ollama restart timed out - skipping")
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "ollama.exe"], capture_output=True, timeout=2
            )
        except Exception:
            pass
        return False
    except Exception as e:
        logger.error(f"Failed to restart Ollama: {e}")
        return False


fact_check_cache = {}


def _google_fact_check(query: str) -> Optional[Dict]:
    cached = fact_check_cache.get(query.lower().strip())
    if cached:
        return cached
    try:
        params = {"query": query[:200], "key": ""}
        resp = requests.get(
            "https://toolbox.google.com/factcheck/api/v1/claimsearch",
            params=params,
            timeout=4,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code == 200:
            data = resp.json()
            claims = []
            results = []
            for item in data if isinstance(data, list) else data:
                if isinstance(item, dict):
                    results.append(item)
            for r in results[:3]:
                text = r.get("text", "") or r.get("claim", "") or ""
                rating = (
                    r.get("claimReview", [{}])[0].get("textualRating", "")
                    if r.get("claimReview")
                    else ""
                )
                publisher = (
                    r.get("claimReview", [{}])[0].get("publisher", {}).get("name", "")
                    if r.get("claimReview")
                    else ""
                )
                if text:
                    claims.append(
                        {
                            "claim": text[:200],
                            "rating": rating[:100],
                            "source": publisher[:50],
                        }
                    )
            if claims:
                fact_check_cache[query.lower().strip()] = claims
                return claims
    except Exception as e:
        logger.debug(f"Fact check API error: {e}")
    return None


RSS_FEEDS = [
    ("http://feeds.bbci.co.uk/news/rss.xml", "BBC News"),
    ("https://news.google.com/rss", "Google News"),
]

TRUSTED_NEWS_SOURCES = [
    {"name": "The Hindu", "domain": "thehindu.com"},
    {"name": "The Indian Express", "domain": "indianexpress.com"},
    {"name": "Press Information Bureau", "domain": "pib.gov.in"},
    {"name": "PTI", "domain": "ptinews.com"},
    {"name": "Reuters", "domain": "reuters.com"},
    {"name": "Associated Press", "domain": "apnews.com"},
    {"name": "BBC News", "domain": "bbc.com"},
    {"name": "NDTV", "domain": "ndtv.com"},
    {"name": "Hindustan Times", "domain": "hindustantimes.com"},
    {"name": "India Today", "domain": "indiatoday.in"},
    {"name": "The Economic Times", "domain": "economictimes.indiatimes.com"},
    {"name": "Mint", "domain": "livemint.com"},
]

ROLE_CLAIM_WORDS = {
    "chief",
    "minister",
    "prime",
    "president",
    "governor",
    "deputy",
    "home",
    "finance",
    "defence",
    "external",
    "affairs",
}

PLACE_CLAIM_WORDS = {
    "assam",
    "bihar",
    "delhi",
    "india",
    "karnataka",
    "kerala",
    "maharashtra",
    "odisha",
    "punjab",
    "rajasthan",
    "tamil",
    "nadu",
    "uttar",
    "pradesh",
    "west",
    "bengal",
}

STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "been",
    "could",
    "during",
    "enter",
    "from",
    "has",
    "have",
    "into",
    "news",
    "not",
    "official",
    "only",
    "over",
    "said",
    "says",
    "should",
    "that",
    "the",
    "this",
    "through",
    "was",
    "were",
    "will",
    "with",
}


def _meaningful_query_words(query: str) -> set:
    return {
        w
        for w in re.findall(r"[a-z0-9]+", query.lower())
        if len(w) > 3 and w not in STOPWORDS
    }


def _build_search_query(text: str, limit: int = 8) -> str:
    terms = _extract_evidence_terms(text, limit)
    return " ".join(terms) if terms else text[:160]


def _relevance_score(query: str, title: str, summary: str = "") -> float:
    query_terms = _meaningful_query_words(query)
    if not query_terms:
        return 0.0
    haystack = f"{title} {summary}".lower()
    matched = {term for term in query_terms if term in haystack}
    title_lower = title.lower()
    title_matches = {term for term in query_terms if term in title_lower}
    score = (len(matched) / max(len(query_terms), 1)) * 100
    score += min(20, len(title_matches) * 4)
    return round(min(score, 100.0), 1)


def _claim_anchor_terms(text: str) -> List[str]:
    terms = list(_meaningful_query_words(text))
    if not any(role in terms for role in ROLE_CLAIM_WORDS):
        return []
    anchors = [
        term
        for term in terms
        if term not in ROLE_CLAIM_WORDS and term not in PLACE_CLAIM_WORDS
    ]
    return anchors[:4]


def _source_matches_claim(news_text: str, title: str, summary: str = "") -> bool:
    anchors = _claim_anchor_terms(news_text)
    if not anchors:
        return True
    haystack = f"{title} {summary}".lower()
    matches = sum(
        1 for term in anchors if re.search(r"\b" + re.escape(term) + r"\b", haystack)
    )
    required = min(2, len(anchors))
    return matches >= required


def _fetch_google_news_search(
    news_text: str, search_query: str, source: Dict[str, str], limit: int = 2
) -> List[Dict[str, Any]]:
    if not HAS_FEEDPARSER:
        return []
    q = quote_plus(f"{search_query} site:{source['domain']}")
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        resp = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return []
        feed = feedparser.parse(resp.content)
        items = []
        for entry in feed.entries[:6]:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "") or ""
            if not _source_matches_claim(news_text, title, summary):
                continue
            score = _relevance_score(search_query, title, summary)
            if score < 35:
                continue
            items.append(
                {
                    "title": title[:180],
                    "source": source["name"],
                    "domain": source["domain"],
                    "url": entry.get("link", ""),
                    "published": entry.get("published", "")[:16],
                    "relevance": score,
                    "trusted": True,
                }
            )
            if len(items) >= limit:
                break
        return items
    except Exception as e:
        logger.debug(f"Trusted source search error ({source['name']}): {e}")
        return []


def _search_trusted_sources(news_text: str) -> List[Dict[str, Any]]:
    search_query = _build_search_query(news_text)
    cache_key = "trusted_" + search_query.lower().strip()
    cached = fact_check_cache.get(cache_key)
    if cached:
        return cached

    results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(
                _fetch_google_news_search, news_text, search_query, source, 1
            )
            for source in TRUSTED_NEWS_SOURCES
        ]
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                logger.debug(f"Trusted source worker error: {e}")

    deduped = []
    seen = set()
    for item in sorted(results, key=lambda x: x.get("relevance", 0), reverse=True):
        key = (item.get("title", "").lower(), item.get("source", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= 5:
            break

    fact_check_cache[cache_key] = deduped
    return deduped


def _fetch_rss_news(query: str) -> list:
    if not HAS_FEEDPARSER:
        return []
    cached = fact_check_cache.get("rss_" + query.lower().strip())
    if cached:
        return cached
    query_words = _meaningful_query_words(query)
    if not query_words:
        return []
    results = []
    for feed_url, source_name in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = entry.get("summary", "") or entry.get("description", "") or ""
                combined = (title + " " + summary).lower()
                match_count = sum(1 for w in query_words if w in combined)
                required_matches = 1 if len(query_words) == 1 else 2
                if match_count >= required_matches:
                    results.append(
                        {
                            "title": title[:150],
                            "source": source_name,
                            "url": entry.get("link", ""),
                            "published": entry.get("published", "")[:16],
                        }
                    )
                    if len(results) >= 3:
                        break
        except Exception as e:
            logger.debug(f"RSS feed error ({source_name}): {e}")
    if results:
        fact_check_cache["rss_" + query.lower().strip()] = results
    return results


def _search_news(query: str) -> list:
    if not NEWS_API_KEY:
        return []
    cached = fact_check_cache.get("news_" + query.lower().strip())
    if cached:
        return cached
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query[:200],
                "apiKey": NEWS_API_KEY,
                "pageSize": 5,
                "sortBy": "relevancy",
                "language": "en",
            },
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get("articles", [])
            results = []
            for a in articles[:3]:
                results.append(
                    {
                        "title": a.get("title", "")[:150],
                        "source": a.get("source", {}).get("name", ""),
                        "url": a.get("url", ""),
                        "published": a.get("publishedAt", "")[:10],
                    }
                )
            if results:
                fact_check_cache["news_" + query.lower().strip()] = results
                return results
    except Exception as e:
        logger.debug(f"NewsAPI error: {e}")
    return []


def _news_api_fetch_relevant(news_text: str) -> List[Dict[str, Any]]:
    """Fetch top relevant News API articles for the claim.
    Returns a list of articles sorted by relevance — used to build context for the LLM."""
    if not NEWS_API_KEY:
        return []
    cache_key = "ctx_" + news_text.lower().strip()[:120]
    cached = fact_check_cache.get(cache_key)
    if cached is not None:
        return cached

    query = _build_search_query(news_text, limit=6)
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "apiKey": NEWS_API_KEY,
                "pageSize": 10,
                "sortBy": "relevancy",
                "language": "en",
            },
            timeout=8,
        )
        if resp.status_code != 200:
            fact_check_cache[cache_key] = []
            return []
        articles = resp.json().get("articles", [])

        results = []
        for a in articles[:10]:
            title = (a.get("title") or "").strip()
            desc = (a.get("description") or "").strip()
            if not title:
                continue
            score = _relevance_score(news_text, title, desc)
            if score >= 25:
                results.append({
                    "score": score,
                    "title": title[:200],
                    "description": desc[:180],
                    "source": (a.get("source") or {}).get("name", ""),
                    "url": a.get("url", ""),
                    "published": (a.get("publishedAt") or "")[:10],
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:5]
        fact_check_cache[cache_key] = results
        return results
    except Exception as e:
        logger.debug(f"News API fetch error: {e}")
        return []


def _parse_verdict(text: str) -> tuple:
    upper = text.upper()

    verdict_match = re.search(
        r"VERDICT\s*:\s*(REAL|FAKE|TRUE|FALSE|MISINFORMATION|LIE|TRUTH|MOSTLY\s*TRUE|MOSTLY\s*FALSE)",
        upper,
    )
    if verdict_match:
        v = verdict_match.group(1).strip()
        if v in ("TRUE", "TRUTH", "REAL", "MOSTLY TRUE"):
            return "REAL"
        if v in ("FALSE", "MISINFORMATION", "LIE", "MOSTLY FALSE"):
            return "FAKE"

    lines = text.split("\n")
    for line in lines[:6]:
        lu = line.strip().upper()
        if (
            lu.startswith("FAKE")
            or "THIS IS FAKE" in lu
            or "CLASSIFICATION: FAKE" in lu
        ):
            return "FAKE"
        if (
            lu.startswith("REAL")
            or "THIS IS REAL" in lu
            or "CLASSIFICATION: REAL" in lu
        ):
            return "REAL"

    if "NOT FAKE" in upper or "NOT FALSE" in upper or "NOT MISINFORMATION" in upper:
        return "REAL"
    if "NOT REAL" in upper or "NOT TRUE" in upper or "NOT ACCURATE" in upper:
        return "FAKE"

    fake_count = len(re.findall(r"\bFAKE\b", upper))
    real_count = len(re.findall(r"\bREAL\b", upper))
    misinfo = len(re.findall(r"\bMISINFORMATION\b", upper))
    false_count = len(re.findall(r"\bFALSE\b", upper))

    fake_score = fake_count * 3 + misinfo * 2 + false_count * 2
    real_score = real_count * 2

    if fake_score > real_score:
        return "FAKE"
    if real_score > fake_score:
        return "REAL"

    return None


def _extract_confidence(text: str) -> float:
    conf_match = re.search(r"CONFIDENCE\s*:\s*(\d+\.?\d*)", text, re.IGNORECASE)
    if conf_match:
        try:
            val = float(conf_match.group(1))
            return max(50.0, min(99.9, val))
        except ValueError:
            pass

    pct_match = re.search(r"(\d+\.?\d*)\s*%", text)
    if pct_match:
        try:
            val = float(pct_match.group(1))
            return max(50.0, min(99.9, val))
        except ValueError:
            pass

    return 88.0


def _extract_explanation(text: str) -> str:
    exp_match = re.search(r"EXPLANATION\s*:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
    if exp_match:
        exp = exp_match.group(1).strip()
    elif "Why:" in text:
        idx = text.index("Why:")
        exp = text[idx + 4 :].strip()
    elif "Explanation:" in text:
        idx = text.index("Explanation:")
        exp = text[idx + 12 :].strip()
    else:
        for trigger in ["Because", "The reason", "This is", "Based on", "Analysis"]:
            if trigger.lower() in text.lower():
                idx = text.lower().index(trigger.lower())
                exp = text[idx:].strip()
                break
        else:
            exp = text[:400].strip()

    exp = re.sub(r"VERDICT\s*:.*?\n", "", exp, flags=re.IGNORECASE).strip()
    exp = re.sub(r"CONFIDENCE\s*:.*?\n", "", exp, flags=re.IGNORECASE).strip()
    return exp[:500]


def _extract_evidence_terms(text: str, limit: int = 6) -> List[str]:
    words = [
        w
        for w in re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower())
        if len(w) > 3 and w not in STOPWORDS
    ]
    seen = []
    for word in words:
        if word not in seen:
            seen.append(word)
        if len(seen) >= limit:
            break
    return seen


def _format_issues(issues: List[Dict[str, Any]], limit: int = 2) -> str:
    details = [i.get("issue", "") for i in issues if i.get("issue")]
    return "; ".join(details[:limit])


def _classify_category(text: str) -> str:
    text_lower = text.lower()
    categories = {
        "sports": [
            "cricket",
            "football",
            "hockey",
            "player",
            "match",
            "rcb",
            "csk",
            "ipl",
            "dhoni",
            "kohli",
        ],
        "indian politics": [
            "chief minister",
            "prime minister",
            "president",
            "minister",
            "bihar",
            "tamil nadu",
            "election",
            "government",
        ],
        "health": [
            "vaccine",
            "covid",
            "medicine",
            "cancer",
            "doctor",
            "hospital",
            "virus",
        ],
        "finance": [
            "stock",
            "market",
            "bank",
            "rbi",
            "repo",
            "rupee",
            "bitcoin",
            "investment",
        ],
        "science": [
            "scientist",
            "research",
            "planet",
            "earth",
            "space",
            "study",
            "climate",
        ],
        "education": ["school", "college", "university", "exam", "student"],
    }
    best = ("general", 0)
    for category, words in categories.items():
        score = sum(1 for word in words if word in text_lower)
        if score > best[1]:
            best = (category, score)
    return best[0]


def _heuristic_only_analysis(news_text: str) -> Dict[str, Any]:
    text_lower = news_text.lower()

    fake_patterns = [
        (
            r"\byou won'?t believe\b",
            "Clickbait: 'you won't believe' is a hallmark of fake news.",
        ),
        (
            r"\bdoctors hate\b",
            "Clickbait: 'doctors hate' phrasing is used to manipulate.",
        ),
        (
            r"\bshocking\b",
            "Sensationalism: overuse of 'shocking' indicates emotional manipulation.",
        ),
        (
            r"\bshare this\b",
            "Viral-manipulation: 'share this' is a common fake news tactic.",
        ),
        (
            r"\bmiracle cure\b",
            "Pseudoscience: 'miracle cure' claims are not medically verified.",
        ),
        (
            r"\bsecret cure\b",
            "Pseudoscience: 'secret cure' implies a conspiracy against known medicine.",
        ),
        (
            r"\bbig pharma\b.*\b(hiding|cover.?up|conspiracy|secret)\b",
            "Conspiracy: 'big pharma hiding' is a common misinformation trope.",
        ),
        (
            r"\bgovernment hiding\b",
            "Conspiracy: 'government hiding' implies unfounded secrecy.",
        ),
        (
            r"\bthey don'?t want you to know\b",
            "Paranoia: 'they don't want you to know' signals manufactured distrust.",
        ),
        (
            r"\bmainstream media won'?t\b",
            "Media distrust: attacking 'mainstream media' is a common disinformation tactic.",
        ),
        (
            r"\bthey are lying\b",
            "Distrust seeding: vague 'they are lying' without evidence.",
        ),
        (
            r"\b100%\s+(guaranteed|proven|safe|effective|certain)\b",
            "Exaggeration: '100% guaranteed' is unrealistic.",
        ),
        (
            r"\bguaranteed\s+(results|returns|cure|profit|money|income)\b",
            "Exaggeration: guaranteed outcomes are not credible.",
        ),
        (
            r"\bdouble\s+your\s+(money|income|investment|profit)\b",
            "Financial scam: guaranteed doubling is a hallmark of fraud.",
        ),
        (
            r"\byou(\s+are)?\s+a\s+winner\b",
            "Scam: 'you are a winner' is a classic phishing/fake tactic.",
        ),
        (
            r"\bcongratulations.*(won|winner|prize)\b",
            "Scam: congratulating on a fake prize.",
        ),
        (
            r"\b(earth|world|planet).*(flat|cube|hollow)\b",
            "Pseudoscience: flat earth / hollow earth conspiracy.",
        ),
        (
            r"\b(vaccine|vaccination|vax).*(microchip|tracking|5g|magnet|bill.gates)\b",
            "Health misinformation: vaccine microchip conspiracy.",
        ),
        (
            r"\b(5g|5\s*g).*(covid|corona|virus|sicken|illness|cancer)\b",
            "Health misinformation: 5G causes illness myth.",
        ),
        (
            r"\bcovid.*(hoax|fake|manufactured|planned|scam|bioweapon)\b",
            "COVID misinformation: pandemic was planned/hoax.",
        ),
        (
            r"\bbill\s*gates.*(patent|vaccine|microchip|control|population|depopulate)\b",
            "Conspiracy: Bill Gates depopulation/control myth.",
        ),
        (
            r"\bms\s+dhoni\b.*\brcb\b",
            "Sports misinformation: MS Dhoni is not an RCB player.",
        ),
        (
            r"\bdhoni\b.*\brcb\s+player\b",
            "Sports misinformation: Dhoni plays for CSK, not RCB.",
        ),
        (
            r"\bvirat\s+kohli\b.*\b(csk|chennai)\b",
            "Sports misinformation: Kohli plays for RCB, not CSK.",
        ),
        (
            r"\brohit\s+sharma\b.*\b(mi|mumbai\s+indians)\s+(released|dropped|sold)\b",
            "Sports misinformation: unlikely transfer rumor.",
        ),
        (
            r"\b(sachin|tendulkar)\b.*\b(comeback|return|unretire)\b",
            "Sports misinformation: unlikely return from retirement.",
        ),
        (
            r"\bmodi\b.*\b(resign|step\s+down|quits)\b",
            "Political misinformation: unsubstantiated resignation claim.",
        ),
        (
            r"\bpresident\b.*\b(dies|dead|assassinated|killed)\b",
            "Death hoax: unverified death of a public figure.",
        ),
        (
            r"\bpm\b.*\b(dies|dead|assassinated|killed|resign)\b",
            "Death/resignation hoax about Prime Minister.",
        ),
        (
            r"\b(chief\s+minister|cm)\b.*\b(resign|arrested|quit)\b",
            "Political hoax: CM resignation or arrest claim.",
        ),
        (
            r"\belection\b.*\b(rigged|fixed|stolen|fraud)\b",
            "Election misinformation: rigged election claim without evidence.",
        ),
        (
            r"\b(foreign\s+power|china|pakistan)\b.*\b(rig|fix|steal|hack)\s+(election|vote)\b",
            "Election interference conspiracy.",
        ),
        (
            r"\breligion?\b.*\b(ban|outlaw|criminalize)\b",
            "Religious misinformation: ban claim without evidence.",
        ),
        (
            r"\btemple\b.*\b(mosque|church)\b.*\b(destroy|demolish|attack)\b",
            "Communal violence: unverified attack claim.",
        ),
        (
            r"\b(muslim|hindu|sikh|christian)\b.*\b(attack|kill|murder)\b.*\b(50|100|200|mass)\b",
            "Communal violence: unsubstantiated mass attack.",
        ),
        (
            r"\b(currency|rupee)\b.*\b(demonetiz|scrap|abolish)\b",
            "Economic misinformation: false demonetization claim.",
        ),
        (
            r"\bbank\b.*\b(crash|collapse|close|failed)\b",
            "Financial panic: false bank failure claim.",
        ),
        (
            r"\bsocial\s+security\b.*\b(end|cancel|eliminate)\b",
            "Welfare misinformation: false benefit cancellation.",
        ),
        (
            r"\b(ufo|alien|extraterrestrial)\b.*\b(government|nasa|confirmed|admitted|cover.up)\b",
            "UFO conspiracy: government cover-up claim.",
        ),
        (
            r"\blizard\b.*\b(children|blood|sacrifice|ritual)\b",
            "Extreme conspiracy: lizard people / blood ritual.",
        ),
        (
            r"\b(illuminati|new\s+world\s+order|deep\s+state)\b",
            "Conspiracy: New World Order / Deep State tropes.",
        ),
        (
            r"\b(chemtrail|geoengineer|weather\s+control)\b",
            "Conspiracy: chemtrail / weather control myth.",
        ),
        (
            r"\b(climate|global\s+warming)\b.*\b(hoax|fake|scam|lie)\b",
            "Climate misinformation: global warming hoax claim.",
        ),
        (
            r"\b(holocaust|genocide)\b.*\b(hoax|fake|exaggerat|myth)\b",
            "Historical denial: holocaust/genocide denial.",
        ),
        (
            r"\b(one\s+simple\s+trick|this\s+one\s+trick)\b",
            "Clickbait: 'one simple trick' is a known fake news pattern.",
        ),
        (
            r"\b(won'?t\s+believe|can'?t\s+believe|don'?t\s+believe)\b",
            "Clickbait: disbelieve-headlines are clickbait.",
        ),
        (
            r"\bwhat\s+happens?\s+next\b",
            "Clickbait: 'what happens next' is a clickbait formula.",
        ),
        (
            r"\bchange\s+your\s+life\s+forever\b",
            "Exaggeration: overpromising life changes.",
        ),
        (
            r"\bsign\s+this\s+petition\b",
            "Manipulation: petition-driving content often contains misinformation.",
        ),
        (
            r"\b(pass\s+this\s+on|forward\s+this|send\s+this\s+to\s+\d+)\b",
            "Chain-mail: forwarding chains are typical of misinformation.",
        ),
        (r"\b(转发|share|转发给)\b", "Chinese chain-mail patterns."),
        (
            r"\baccording\s+to\s+(anonymous|unnamed|unnamed\s+sources?|inside\s+sources?)\b",
            "Vague sourcing: anonymous sources without attribution.",
        ),
        (r"\bsources?\s+say\b", "Vague sourcing: no specific source named."),
        (
            r"\bbreaking\s+news\b.*\b(just\s+in|developing)\b",
            "Urgency: 'breaking news' without named outlet.",
        ),
        (
            r"\b(urgent|emergency|immediate)\s+(alert|warning|notice|action)\b",
            "Urgency: urgent alert without clear source.",
        ),
        (
            r"\bthis\s+is\s+not\s+a\s+drill\b",
            "False urgency: 'this is not a drill' is often misinformation.",
        ),
        (
            r"\beveryone\s+(is\s+)?(saying|talking|discussing)\b",
            "Bandwagon: 'everyone is saying' implies false consensus.",
        ),
        (
            r"\byou\s+won'?t\s+see\s+this\s+(on|in)\s+(mainstream|news|tv|media)\b",
            "Media distrust: 'suppressed by mainstream media'.",
        ),
        (
            r"\bthey\s+(don'?t|cannot)\s+(handle|deal\s+with|silence)\s+(the\s+)?truth\b",
            "Persecution complex: 'they can't handle the truth'.",
        ),
        (
            r"\bwake\s+up\s+(sheeple|people|america|india)\b",
            "Condescension: 'wake up' rhetoric common in conspiracy.",
        ),
        (
            r"\bdo\s+(your\s+own\s+research|the\s+research|the\s+homework)\b",
            "Anti-expert: 'do your own research' dismissal of experts.",
        ),
        (
            r"\bopen\s+your\s+eyes\b",
            "Conspiracy: 'open your eyes' implies hidden truth.",
        ),
        (
            r"\bthe\s+truth\s+(about|behind|of)\b",
            "Conspiracy: 'the truth about' implies hidden information.",
        ),
        (
            r"\bwhat\s+they\s+don'?t\s+(want\s+you|tell\s+you)\b",
            "Conspiracy: 'what they don't want you to know'.",
        ),
        (
            r"\b(doctors|scientists|experts)\s+(hate|don'?t\s+want|are\s+hiding)\b",
            "Anti-expert: professional hate/hide claims.",
        ),
        (
            r"\b(secret|hidden|censored)\s+(report|study|research|document|video|footage)\b",
            "Suppressed content: hidden document trope.",
        ),
        (
            r"\bproven\s+(wrong|false|incorrect|debunked)\b",
            "Denial: 'proven wrong' dismissal of established facts.",
        ),
    ]

    real_patterns = [
        (
            r"\b(according\s+to|said|stated|reported\s+by)\s+(Reuters|AP\s+News|Associated\s+Press|BBC|CNN|NDTV|The\s+Hindu|Indian\s+Express|Times\s+of\s+India|Hindustan\s+Times)\b",
            "Cited credible news source.",
        ),
        (
            r"\bstudy\s+(published|by|from|in)\s+(Nature|Science|Lancet|NEJM|BMJ|JAMA|Cell|PNAS)\b",
            "References a peer-reviewed journal.",
        ),
        (
            r"\baccording\s+to\s+(data|statistics|figures|research|survey)\s+(from|by|released|published)\b",
            "Cites verifiable data.",
        ),
        (
            r"\b(government|official|ministry|department)\s+(spokesperson|release|statement|report|data)\b",
            "Cites official government source.",
        ),
        (r"\bcourt\s+(rules|orders|says|dismisses|upholds)\b", "Cites court ruling."),
        (
            r"\b(police|investigat|probe|inquiry)\s+(said|found|confirmed|revealed)\b",
            "Cites law enforcement investigation.",
        ),
    ]

    fake_score = 0
    fake_reasons = []
    for pattern, reason in fake_patterns:
        if re.search(pattern, text_lower):
            fake_score += 1
            if len(fake_reasons) < 3:
                fake_reasons.append(reason)

    real_score = 0
    real_reasons = []
    for pattern, reason in real_patterns:
        if re.search(pattern, text_lower):
            real_score += 1
            if len(real_reasons) < 2:
                real_reasons.append(reason)

    emotional_words = [
        "outrage",
        "disgust",
        "appalled",
        "shocked",
        "terrified",
        "furious",
        "heartbreaking",
        "devastated",
        "unbelievable",
        "incredible",
        "mind-blowing",
        "jaw-dropping",
        "unthinkable",
        "nightmare",
        "horrifying",
        "sickening",
        "disgraceful",
        "appalling",
        "abomination",
        "catastrophe",
        "disaster",
        "horrific",
        "tragic",
        "agonizing",
        "excruciating",
        "insufferable",
    ]
    emotional_count = sum(1 for w in emotional_words if w in text_lower)
    if emotional_count >= 3:
        fake_score += 2
        if len(fake_reasons) < 3:
            fake_reasons.append(
                f"High emotional language ({emotional_count} emotional words found) — common in fake news."
            )
    elif emotional_count >= 1:
        fake_score += 0.5

    exclamation_count = text_lower.count("!!!")
    if exclamation_count >= 2:
        fake_score += 1
        if len(fake_reasons) < 3:
            fake_reasons.append(
                "Multiple exclamation marks — hallmark of sensationalist misinformation."
            )

    all_caps_words = len(re.findall(r"\b[A-Z]{4,}\b", news_text))
    if all_caps_words >= 3:
        fake_score += 1
        if len(fake_reasons) < 3:
            fake_reasons.append(
                "Excessive SHOUTING in all-caps words — common in fake news."
            )

    if fake_score > real_score:
        prediction = "FAKE"
        raw_conf = 75.0 + min(20.0, fake_score * 3.0)
        confidence = min(95.0, raw_conf)
    elif real_score > fake_score and real_score >= 2:
        prediction = "REAL"
        raw_conf = 70.0 + min(20.0, real_score * 5.0)
        confidence = min(90.0, raw_conf)
    else:
        prediction = "UNSURE"
        confidence = 55.0

    if prediction == "UNSURE":
        # Unknown claims default to REAL with low confidence — do NOT penalise recency
        prediction = "REAL"
        confidence = max(58.0, confidence)
        fake_reasons.append(
            "No misinformation signals detected. Insufficient evidence to confirm or deny — treating as potentially real."
        )

    explanation_parts = []
    if prediction == "FAKE":
        if fake_reasons:
            explanation_parts.append(
                "Misinformation signals detected: " + " ".join(fake_reasons[:3])
            )
        if real_reasons and fake_reasons:
            explanation_parts.append(
                "Note: Some credible-source signals were found, but the misinformation signals outweigh them."
            )
        if not fake_reasons and not real_reasons:
            explanation_parts.append(
                "The article could not be verified against any reliable sources and is therefore classified as suspicious."
            )
    else:
        explanation_parts.append("Credible-source signals: " + " ".join(real_reasons))
        if fake_reasons:
            explanation_parts.append(
                "Note: Some suspicious patterns were also detected but outweighed by credible signals."
            )

    explanation = (
        " ".join(explanation_parts)
        if explanation_parts
        else "Analysis completed with limited signals."
    )

    return {
        "prediction": prediction,
        "confidence": round(confidence, 1),
        "explanation": explanation[:600].strip(),
        "method": "Local heuristic fallback",
        "category": _classify_category(news_text),
        "reasons": fake_reasons + real_reasons,
    }


def _clean_sentence(text: str, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = re.sub(r"\s*\.\s*\.", ".", text)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(".,;") + "."


def _claim_summary(news_text: str, limit: int = 260) -> str:
    text = _clean_sentence(news_text, limit)
    return text if text else "the submitted news text"


def _verdict_explanation(
    prediction: str,
    news_text: str,
    category: str,
    kb_result: Dict[str, Any],
    llm_verdict: Optional[str] = None,
    llm_exp: str = "",
    fact_note: str = "",
    trusted_sources: Optional[List[Dict[str, Any]]] = None,
) -> str:
    evidence_terms = _extract_evidence_terms(news_text)
    subject = ", ".join(evidence_terms[:4]) if evidence_terms else "the submitted text"
    issues = [
        _clean_sentence(i.get("issue", ""), 220)
        for i in kb_result.get("issues", [])
        if i.get("issue")
    ]
    claim = _claim_summary(news_text)
    verdict_word = "false or misleading" if prediction == "FAKE" else "real / supported"

    agreement = "No cloud AI verdict was available, so the final result used the local AI/heuristic fallback and external evidence."
    if llm_verdict:
        agreement = (
            f"The AI model also classified the article as {prediction}, so it agrees with the final verdict."
            if llm_verdict == prediction
            else f"The AI model initially classified it as {llm_verdict}, but the final result was changed to {prediction} because stronger fact-check or trusted-source evidence contradicted that model output."
        )

    trusted_sources = trusted_sources or []
    trusted_titles = []
    for item in trusted_sources[:3]:
        title = _clean_sentence(item.get("title", ""), 160)
        source = item.get("source", "trusted source")
        relevance = item.get("relevance")
        if title:
            trusted_titles.append(
                f"{source}: {title}"
                + (f" ({relevance}% relevance)" if relevance is not None else "")
            )

    reason_parts = []
    if prediction == "FAKE":
        if issues:
            reason_parts.append(
                "Rule/evidence contradiction: " + "; ".join(issues[:3]) + "."
            )
        if llm_exp:
            reason_parts.append("AI reasoning: " + _clean_sentence(llm_exp, 320))
        if fact_note:
            reason_parts.append(
                "External fact-check signal: " + _clean_sentence(fact_note, 320)
            )
        if not reason_parts:
            reason_parts.append(
                "The article contains reliability problems or unverifiable claims that are not supported by the strongest available checks."
            )
    else:
        if fact_note:
            reason_parts.append("External support: " + _clean_sentence(fact_note, 320))
        if trusted_titles:
            reason_parts.append(
                "Trusted-source support: " + " | ".join(trusted_titles[:3]) + "."
            )
        if llm_exp and llm_verdict == prediction:
            reason_parts.append("AI reasoning: " + _clean_sentence(llm_exp, 320))
        if not reason_parts:
            reason_parts.append(
                "No strong contradiction, conspiracy marker, role mismatch, or high-risk misinformation pattern was found in the submitted text."
            )

    if prediction == "FAKE" and trusted_titles:
        reason_parts.append(
            "Important source note: related trusted articles were found, but they do not outweigh the direct contradiction in the submitted claim."
        )

    parts = [
        f"Verdict: {prediction}. The submitted {category} article is classified as {verdict_word}.",
        f'Entered claim analyzed: "{claim}".',
        f"Main reasoning: {' '.join(reason_parts)}",
        f"Model and evidence agreement: {agreement}",
        f"Key terms checked: {subject}.",
    ]
    return "\n\n".join(part.strip() for part in parts if part.strip())


def _smart_fallback(news_text: str) -> Dict[str, Any]:
    return _heuristic_only_analysis(news_text)


def analyze_with_phi3(news_text: str) -> Dict[str, Any]:
    # Step 1: fetch all external evidence in parallel before LLM call
    fact_check_results = _google_fact_check(news_text)
    trusted_results = _search_trusted_sources(news_text)
    news_results = (
        _search_news(news_text) if NEWS_API_KEY else _fetch_rss_news(news_text)
    )
    # Step 2: fetch multiple relevant News API articles for context
    news_api_articles = _news_api_fetch_relevant(news_text) if NEWS_API_KEY else []

    category = _classify_category(news_text)
    fallback_result = _heuristic_only_analysis(news_text)

    # Build rich context string from top-N articles — passed to Groq for reasoning
    recent_context = ""
    if news_api_articles:
        lines = []
        for a in news_api_articles[:4]:
            line = f"- \"{a['title']}\""
            if a.get("description"):
                line += f" | {a['description'][:120]}"
            line += f" (Source: {a['source']}, Published: {a['published']}, Relevance: {a['score']}%)"
            lines.append(line)
        recent_context = "\n".join(lines)
        logger.info(f"News API context: {len(news_api_articles)} articles, top score={news_api_articles[0]['score']}")

    llm_response = None
    llm_source = ""

    groq_raw = groq_client.analyze_with_groq(news_text, recent_context=recent_context)
    groq_structured = {}
    if groq_raw:
        llm_response = groq_raw
        llm_source = "Groq (Llama 3.3 70B)"
        groq_structured = groq_client.parse_groq_structured(groq_raw)
        logger.info("Using Groq API for LLM inference")
    else:
        logger.info("Groq not available, falling back to Ollama Phi-3")
        llm_response = _call_ollama(
            f"""You are a strict AI fact-checker. Determine if the following news text is REAL (factually correct) or FAKE (false/misinformation).

Rules:
- Factual contradictions, role mismatches, conspiracy claims, and manipulative clickbait indicate FAKE.
- Verified facts, ordinary official statements, and measured language indicate REAL.
- Do not mark a short factual statement fake only because it is short.
- Your explanation must mention the specific claim in the news text.

News text: "{news_text}"

Respond EXACTLY:
VERDICT: [REAL or FAKE]
CONFIDENCE: [85-99]
EXPLANATION: [1-2 sentences]"""
        )
        if llm_response:
            llm_source = f"Phi-3 (Local LLM)"

    method = fallback_result["method"]
    prediction = fallback_result["prediction"]
    confidence = fallback_result["confidence"]
    llm_verdict = None
    llm_exp = fallback_result["explanation"]

    if llm_response:
        llm_verdict = _parse_verdict(llm_response)
        llm_conf = _extract_confidence(llm_response)
        llm_exp = _extract_explanation(llm_response)
        if llm_verdict:
            prediction = llm_verdict
            confidence = max(55.0, min(98.0, llm_conf))
            method = llm_source
        else:
            logger.warning("LLM response lacked a clear verdict; using heuristic fallback prediction")
            prediction = fallback_result["prediction"]
            confidence = fallback_result["confidence"]
            method = fallback_result["method"]

    fact_note = ""
    trusted_note = ""
    high_relevance_trusted = [
        r for r in trusted_results if float(r.get("relevance", 0) or 0) >= 45
    ]
    if high_relevance_trusted:
        source_names = ", ".join(
            r.get("source", "trusted source") for r in high_relevance_trusted[:3]
        )
        trusted_note = (
            f"Trusted-source matches from {source_names} were found for this topic."
        )
        if prediction == "REAL":
            confidence = min(98.0, confidence + 5)

    # ── News API context note (display only — Groq already reasoned with the articles) ──
    if news_api_articles:
        best = news_api_articles[0]
        fact_note = (
            f"News API found {len(news_api_articles)} related article(s): "
            f"\"{best['title']}\" from {best['source']} "
            f"({best['published']}, {best['score']}% relevance)."
        )
        # Gentle confidence boost only when LLM already agrees this is REAL
        if prediction == "REAL" and best["score"] >= 55:
            confidence = min(97.0, confidence + 4)
    elif trusted_note:
        fact_note = trusted_note

    # ── Google Fact Check API ────────────────────────────────────────────────
    if fact_check_results:
        fc_info = "; ".join(
            f"{c['claim'][:70]} - {c['rating']}" for c in fact_check_results[:2]
        )
        findings_lower = " ".join(str(f).lower() for f in fact_check_results)
        if any(kw in findings_lower for kw in ["false", "misleading", "fake", "incorrect", "hoax"]):
            prediction = "FAKE"
            confidence = min(99.0, confidence + 8)
            fact_note = f"External fact-check evidence flags it: {fc_info}."
        elif any(kw in findings_lower for kw in ["true", "correct", "accurate", "factual"]):
            prediction = "REAL"
            confidence = min(99.0, confidence + 8)
            fact_note = f"External fact-check evidence supports it: {fc_info}."

    explanation = _verdict_explanation(
        prediction,
        news_text,
        category,
        {"issues": []},
        llm_verdict,
        llm_exp,
        fact_note,
        high_relevance_trusted if prediction == "REAL" else [],
    )

    all_fact_checks = (fact_check_results or [])[:3]
    for a in news_api_articles[:3]:
        all_fact_checks.insert(0, {
            "claim": a["title"],
            "rating": f"Live News API context ({a['score']}% relevance)",
            "source": a["source"],
            "url": a.get("url", ""),
            "published": a.get("published", ""),
            "trusted": a["score"] >= 55,
        })
    for t in trusted_results[:5]:
        all_fact_checks.append(
            {
                "claim": t["title"],
                "rating": f"Trusted source match ({t.get('relevance', 0)}%)",
                "source": t["source"],
                "url": t.get("url", ""),
                "published": t.get("published", ""),
                "trusted": True,
            }
        )
    for a in (news_results or [])[:2]:
        all_fact_checks.append(
            {
                "claim": a["title"],
                "rating": "Referenced",
                "source": a["source"],
                "url": a.get("url", ""),
                "published": a.get("published", ""),
            }
        )

    if not llm_response and not groq_raw:
        method = fallback_result["method"]

    # Pull structured XAI fields from Groq response when available
    xai_reasons = groq_structured.get("reasons", [])
    xai_suspicious = groq_structured.get("suspicious_phrases", [])
    manipulation_type = groq_structured.get("manipulation_type", "None")

    return {
        "prediction": prediction,
        "confidence": round(confidence, 1),
        "explanation": explanation[:1800].strip(),
        "method": method,
        "fact_checks": all_fact_checks,
        "llm_source": llm_source,
        "category": category.title(),
        "model_verdict": llm_verdict,
        "trusted_source_count": len(trusted_results),
        "xai_reasons": xai_reasons,
        "xai_suspicious_phrases": xai_suspicious,
        "manipulation_type": manipulation_type,
        "news_api_articles": news_api_articles[:4],
    }


def check_ollama_status() -> Dict[str, Any]:
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            names = [m.get("name", "") for m in models]
            primary_ok = any(PRIMARY_MODEL in n for n in names)
            fast_ok = any(FAST_MODEL in n for n in names)
            return {
                "running": True,
                "primary_available": primary_ok,
                "fast_model_available": fast_ok,
                "active_model": PRIMARY_MODEL
                if primary_ok
                else (FAST_MODEL if fast_ok else "none"),
                "models": names,
            }
        return {"running": False, "error": "API not responding"}
    except requests.exceptions.ConnectionError:
        return {"running": False, "error": "Ollama not running"}
    except requests.exceptions.Timeout:
        return {"running": False, "error": "Ollama server hung"}
    except Exception as e:
        return {"running": False, "error": str(e)}
