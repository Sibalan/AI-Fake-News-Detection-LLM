import os
import sys
from backend.knowledge_base import verify_from_knowledge_base
from backend.fact_checker.claim_extractor import extract_claim
from backend.fact_checker.evidence_retriever import retrieve_evidence
from backend.fact_checker.evidence_filter import filter_evidence
from backend.fact_checker.llm_reasoner import reason_over_evidence
from backend.fact_checker.verdict_engine import combine_verdicts
import requests
from datetime import datetime, timezone
import json
import re
from event_matcher import event_match
import logging
import os
import subprocess
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus
from typing import Dict, Any, Optional, List
from backend.config import Config
from backend import groq_client
from backend.claim_extractor import extract_claim
from backend.category_detector import detect_category
from backend.knowledge_resolver import resolve_knowledge
from backend.decision_engine import decide_verdict
from backend.claim_verifier import verify_roles

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

logger = logging.getLogger(__name__)

RSS_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.7",
}
_RSS_FEED_ERRORS_LOGGED = set()

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
PRIMARY_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
FAST_MODEL = "tinyllama:latest"


def safe_requests_get(url: str, timeout: int = Config.RSS_FETCH_TIMEOUT, headers: Optional[dict] = None):
    try:
        response = requests.get(
            url,
            headers={**RSS_REQUEST_HEADERS, **(headers or {})},
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        if url not in _RSS_FEED_ERRORS_LOGGED:
            logger.warning(f"RSS request failed for {url}: {exc}")
            _RSS_FEED_ERRORS_LOGGED.add(url)
        return None


NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

VISION_MODEL_BLACKLIST = set()


def _is_vision_model(model_name: str) -> bool:
    vision_keywords = [
        "llava", "bakllava", "cogvlm", "moondream", "minicpm-v", "phi3-v", "vision",
    ]
    name_lower = model_name.lower()
    for kw in vision_keywords:
        if kw in name_lower:
            return True
    return False


def _try_inference(model: str, prompt: str, max_tokens: int, timeout: int) -> Optional[str]:
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

            print("\n========================")
            print("Trying model:", model)
            print("Endpoint:", fmt)
            print("Status Code:", resp.status_code)

            try:
                print("Response JSON:")
                print(resp.json())
            except Exception:
                print("Raw Response:")
                print(resp.text)

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


def _call_ollama(prompt: str, max_tokens: int = 400):
    print("\n===== ENTERED _call_ollama =====")

    try:
        print("Checking Ollama server...")
        alive = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        print("Status:", alive.status_code)
        if alive.status_code != 200:
            print("Health check failed")
            return None
    except Exception as e:
        print("Health check exception:")
        print(e)
        return None

    print("Health check OK")
    print("Calling PRIMARY MODEL...")

    result = _try_inference(PRIMARY_MODEL, prompt, max_tokens, 30)

    print("Returned from PRIMARY MODEL:")
    print(result)

    if result:
        return result

    print("Trying FALLBACK MODEL...")

    result = _try_inference(FAST_MODEL, prompt, max_tokens, 20)

    print("Returned from FALLBACK MODEL:")
    print(result)

    return result


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
    ("https://feeds.feedburner.com/ndtvnews-top-stories", "NDTV"),
    ("https://indianexpress.com/section/india/feed/", "The Indian Express"),
    ("https://www.news18.com/rss/india.xml", "News18"),
    ("https://www.theguardian.com/world/rss", "The Guardian"),
    ("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera"),
    ("https://www.timesofindia.indiatimes.com/rssfeedstopstories.cms", "Times of India"),
    ("http://rss.cnn.com/rss/edition.rss", "CNN"),
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
    "chief", "minister", "prime", "president", "governor", "deputy",
    "home", "finance", "defence", "external", "affairs",
}

PLACE_CLAIM_WORDS = {
    "assam", "bihar", "delhi", "india", "karnataka", "kerala",
    "maharashtra", "odisha", "punjab", "rajasthan", "tamil",
    "nadu", "uttar", "pradesh", "west", "bengal",
}

STOPWORDS = {
    "about", "after", "also", "and", "are", "been", "could", "during",
    "enter", "from", "has", "have", "into", "news", "not", "official",
    "only", "over", "said", "says", "should", "that", "the", "this",
    "through", "was", "were", "will", "with",
}

SPECIAL_QUERY_TOKENS = {
    "ipl", "rcb", "csk", "mi", "srh", "pbks", "kkr", "dc", "tamil",
    "nadu", "stalin", "mk", "cm", "pm", "bjp", "inc", "modi", "gandhi",
    "ai", "covid", "nasa", "us", "uk", "eu", "china", "pakistan",
}


def _meaningful_query_words(query: str) -> set:
    words = set()
    for w in re.findall(r"[a-z0-9]+", query.lower()):
        if w in STOPWORDS:
            continue
        if len(w) > 3 or w in SPECIAL_QUERY_TOKENS:
            words.add(w)
        elif len(w) == 3 and w.isalpha():
            words.add(w)
    return words


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


def _claim_consistency(news_text: str, title: str, summary: str = "") -> str:
    claim = news_text.lower().strip()
    article = f"{title} {summary}".lower()

    # Verify role consistency first
    role_result = verify_roles(news_text, article)

    if role_result == "SUPPORT":
        print("Role Match: SUPPORT")
        return "SUPPORT"

    if role_result == "CONTRADICT":
        print("Role Match: CONTRADICT")
        return "CONTRADICT"

    contradiction_words = [
        "former",
        "ex-",
        "ex ",
        "resigned",
        "quit",
        "removed",
        "replaced",
        "defeated",
        "lost election",
        "no longer",
        "stepped down",
        "ceased",
        "suspended",
        "dismissed",
        "dead",
        "died",
        "fake",
        "false",
        "incorrect",
        "misleading",
        "hoax",
        "rumour",
        "rumor",
        "denied",
        "refuted",
        "debunked",
    ]

    for word in contradiction_words:
        if word in article:
            return "CONTRADICT"

    status, score = event_match(news_text, article)

    print("Claim:", claim)
    print("Article:", article)
    print("Event Match:", status)
    print("Similarity:", score)

    if status == "SUPPORT":
        return "SUPPORT"

    if status == "CONTRADICT":
        return "CONTRADICT"

    # A partial match is not enough to verify the claim.
    # Treat it as irrelevant so it doesn't become supporting evidence.
    if status == "PARTIAL":
        return "IRRELEVANT"

    return "IRRELEVANT"

def _claim_support_score(news_text: str, title: str, summary: str = "") -> float:
    terms = _extract_evidence_terms(news_text, limit=10)
    if not terms:
        return 0.0
    haystack = f"{title} {summary}".lower()
    matches = sum(1 for term in terms if re.search(r"\b" + re.escape(term) + r"\b", haystack))
    return round(100.0 * matches / len(terms), 1)


def _is_political_office_claim(text: str) -> bool:
    text_lower = text.lower()
    patterns = [
        r"\b(chief minister|cm|prime minister|pm|president|governor|minister|speaker|mayor)\b.*\b(is|was|becomes|became|appointed|named)\b.*\b([a-z][a-z]+)\b",
        r"\b([a-z][a-z]+(?:\s+[a-z][a-z]+)*)\b.*\b(is|was|becomes|became|appointed|named)\b.*\b(chief minister|cm|prime minister|president|governor|minister|speaker|mayor)\b",
        r"\b(chief minister|cm|prime minister|president|governor|minister|speaker|mayor)\b.*\b(of|for|in)\b.*\b(tamil nadu|bihar|uttar pradesh|maharashtra|karnataka|kerala|delhi|gujarat|punjab|haryana|rajasthan)\b",
    ]
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def _fetch_google_news_search(
    news_text: str, search_query: str, source: Dict[str, str], limit: int = 2
) -> List[Dict[str, Any]]:
    if not HAS_FEEDPARSER:
        return []
    q = quote_plus(f"{search_query} site:{source['domain']}")
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        resp = safe_requests_get(url, timeout=5)
        if resp is None:
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
            resp = safe_requests_get(feed_url)
            if resp is None:
                continue
            feed = feedparser.parse(resp.content)
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
        if lu.startswith("FAKE") or "THIS IS FAKE" in lu or "CLASSIFICATION: FAKE" in lu:
            return "FAKE"
        if lu.startswith("REAL") or "THIS IS REAL" in lu or "CLASSIFICATION: REAL" in lu:
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


def _parse_published_date(s: str) -> Optional[datetime]:
    if not s:
        return None
    s = s.strip()
    try:
        from dateutil import parser as dateutil_parser
        dt = dateutil_parser.parse(s, fuzzy=True)
        if dt:
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
    except Exception:
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(s)
            if dt:
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt
        except Exception:
            pass

    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s.split("+")[0].split("Z")[0].strip(), fmt)
            return dt
        except Exception:
            continue

    m = re.search(
        r"(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*)?(?P<day>\d{1,2})\s+(?P<mon>[A-Za-z]+)\s+(?P<year>\d{4})", s
    )
    if m:
        mon = m.group("mon").lower()
        months = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
        }
        try:
            day = int(m.group('day'))
            year = int(m.group('year'))
            month_num = months.get(mon[:3], None) or months.get(mon, None)
            if month_num:
                return datetime(year, month_num, day)
        except Exception:
            pass

    m = re.search(r"(20\d{2}|19\d{2})", s)
    if m:
        try:
            y = int(m.group(1))
            return datetime(y, 1, 1)
        except Exception:
            return None
    return None


def _is_recent(published: str, days: int = 30) -> bool:
    dt = _parse_published_date(published)
    if not dt:
        return False
    try:
        delta = datetime.utcnow() - dt
        return delta.total_seconds() >= 0 and delta.days <= days
    except Exception:
        return False


def _extract_explanation(text: str) -> str:
    exp_match = re.search(r"EXPLANATION\s*:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
    if exp_match:
        exp = exp_match.group(1).strip()
    elif "Why:" in text:
        idx = text.index("Why:")
        exp = text[idx + 4:].strip()
    elif "Explanation:" in text:
        idx = text.index("Explanation:")
        exp = text[idx + 12:].strip()
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
        for w in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if (len(w) >= 3 and (w not in STOPWORDS or w in SPECIAL_QUERY_TOKENS))
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
            "cricket", "football", "hockey", "player", "match",
            "rcb", "csk", "ipl", "dhoni", "kohli",
        ],
        "indian politics": [
            "chief minister", "prime minister", "president", "minister",
            "bihar", "tamil nadu", "election", "government",
        ],
        "health": ["vaccine", "covid", "medicine", "cancer", "doctor", "hospital", "virus"],
        "finance": ["stock", "market", "bank", "rbi", "repo", "rupee", "bitcoin", "investment"],
        "science": ["scientist", "research", "planet", "earth", "space", "study", "climate"],
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
        (r"\byou won'?t believe\b", "Clickbait: 'you won't believe' is a hallmark of fake news."),
        (r"\bdoctors hate\b", "Clickbait: 'doctors hate' phrasing is used to manipulate."),
        (r"\bshocking\b", "Sensationalism: overuse of 'shocking' indicates emotional manipulation."),
        (r"\bshare this\b", "Viral-manipulation: 'share this' is a common fake news tactic."),
        (r"\bmiracle cure\b", "Pseudoscience: 'miracle cure' claims are not medically verified."),
        (r"\bsecret cure\b", "Pseudoscience: 'secret cure' implies a conspiracy against known medicine."),
        (r"\bbig pharma\b.*\b(hiding|cover.?up|conspiracy|secret)\b", "Conspiracy: 'big pharma hiding' is a common misinformation trope."),
        (r"\bgovernment hiding\b", "Conspiracy: 'government hiding' implies unfounded secrecy."),
        (r"\bthey don'?t want you to know\b", "Paranoia: 'they don't want you to know' signals manufactured distrust."),
        (r"\bmainstream media won'?t\b", "Media distrust: attacking 'mainstream media' is a common disinformation tactic."),
        (r"\bthey are lying\b", "Distrust seeding: vague 'they are lying' without evidence."),
        (r"\b100%\s+(guaranteed|proven|safe|effective|certain)\b", "Exaggeration: '100% guaranteed' is unrealistic."),
        (r"\bguaranteed\s+(results|returns|cure|profit|money|income)\b", "Exaggeration: guaranteed outcomes are not credible."),
        (r"\bdouble\s+your\s+(money|income|investment|profit)\b", "Financial scam: guaranteed doubling is a hallmark of fraud."),
        (r"\byou(\s+are)?\s+a\s+winner\b", "Scam: 'you are a winner' is a classic phishing/fake tactic."),
        (r"\bcongratulations.*(won|winner|prize)\b", "Scam: congratulating on a fake prize."),
        (r"\b(earth|world|planet).*(flat|cube|hollow)\b", "Pseudoscience: flat earth / hollow earth conspiracy."),
        (r"\b(vaccine|vaccination|vax).*(microchip|tracking|5g|magnet|bill.gates)\b", "Health misinformation: vaccine microchip conspiracy."),
        (r"\b(5g|5\s*g).*(covid|corona|virus|sicken|illness|cancer)\b", "Health misinformation: 5G causes illness myth."),
        (r"\bcovid.*(hoax|fake|manufactured|planned|scam|bioweapon)\b", "COVID misinformation: pandemic was planned/hoax."),
        (r"\bbill\s*gates.*(patent|vaccine|microchip|control|population|depopulate)\b", "Conspiracy: Bill Gates depopulation/control myth."),
        (r"\bms\s+dhoni\b.*\brcb\b", "Sports misinformation: MS Dhoni is not an RCB player."),
        (r"\bdhoni\b.*\brcb\s+player\b", "Sports misinformation: Dhoni plays for CSK, not RCB."),
        (r"\bvirat\s+kohli\b.*\b(csk|chennai)\b", "Sports misinformation: Kohli plays for RCB, not CSK."),
        (r"\brohit\s+sharma\b.*\b(mi|mumbai\s+indians)\s+(released|dropped|sold)\b", "Sports misinformation: unlikely transfer rumor."),
        (r"\b(sachin|tendulkar)\b.*\b(comeback|return|unretire)\b", "Sports misinformation: unlikely return from retirement."),
        (r"\bmodi\b.*\b(resign|step\s+down|quits)\b", "Political misinformation: unsubstantiated resignation claim."),
        (r"\bpresident\b.*\b(dies|dead|assassinated|killed)\b", "Death hoax: unverified death of a public figure."),
        (r"\bpm\b.*\b(dies|dead|assassinated|killed|resign)\b", "Death/resignation hoax about Prime Minister."),
        (r"\b(chief\s+minister|cm)\b.*\b(resign|arrested|quit)\b", "Political hoax: CM resignation or arrest claim."),
        (r"\belection\b.*\b(rigged|fixed|stolen|fraud)\b", "Election misinformation: rigged election claim without evidence."),
        (r"\b(foreign\s+power|china|pakistan)\b.*\b(rig|fix|steal|hack)\s+(election|vote)\b", "Election interference conspiracy."),
        (r"\breligion?\b.*\b(ban|outlaw|criminalize)\b", "Religious misinformation: ban claim without evidence."),
        (r"\btemple\b.*\b(mosque|church)\b.*\b(destroy|demolish|attack)\b", "Communal violence: unverified attack claim."),
        (r"\b(muslim|hindu|sikh|christian)\b.*\b(attack|kill|murder)\b.*\b(50|100|200|mass)\b", "Communal violence: unsubstantiated mass attack."),
        (r"\b(currency|rupee)\b.*\b(demonetiz|scrap|abolish)\b", "Economic misinformation: false demonetization claim."),
        (r"\bbank\b.*\b(crash|collapse|close|failed)\b", "Financial panic: false bank failure claim."),
        (r"\bsocial\s+security\b.*\b(end|cancel|eliminate)\b", "Welfare misinformation: false benefit cancellation."),
        (r"\b(ufo|alien|extraterrestrial)\b.*\b(government|nasa|confirmed|admitted|cover.up)\b", "UFO conspiracy: government cover-up claim."),
        (r"\blizard\b.*\b(children|blood|sacrifice|ritual)\b", "Extreme conspiracy: lizard people / blood ritual."),
        (r"\b(illuminati|new\s+world\s+order|deep\s+state)\b", "Conspiracy: New World Order / Deep State tropes."),
        (r"\b(chemtrail|geoengineer|weather\s+control)\b", "Conspiracy: chemtrail / weather control myth."),
        (r"\b(climate|global\s+warming)\b.*\b(hoax|fake|scam|lie)\b", "Climate misinformation: global warming hoax claim."),
        (r"\b(holocaust|genocide)\b.*\b(hoax|fake|exaggerat|myth)\b", "Historical denial: holocaust/genocide denial."),
        (r"\b(one\s+simple\s+trick|this\s+one\s+trick)\b", "Clickbait: 'one simple trick' is a known fake news pattern."),
        (r"\b(won'?t\s+believe|can'?t\s+believe|don'?t\s+believe)\b", "Clickbait: disbelieve-headlines are clickbait."),
        (r"\bwhat\s+happens?\s+next\b", "Clickbait: 'what happens next' is a clickbait formula."),
        (r"\bchange\s+your\s+life\s+forever\b", "Exaggeration: overpromising life changes."),
        (r"\bsign\s+this\s+petition\b", "Manipulation: petition-driving content often contains misinformation."),
        (r"\b(pass\s+this\s+on|forward\s+this|send\s+this\s+to\s+\d+)\b", "Chain-mail: forwarding chains are typical of misinformation."),
        (r"\b(转发|share|转发给)\b", "Chinese chain-mail patterns."),
        (r"\baccording\s+to\s+(anonymous|unnamed|unnamed\s+sources?|inside\s+sources?)\b", "Vague sourcing: anonymous sources without attribution."),
        (r"\bsources?\s+say\b", "Vague sourcing: no specific source named."),
        (r"\bbreaking\s+news\b.*\b(just\s+in|developing)\b", "Urgency: 'breaking news' without named outlet."),
        (r"\b(urgent|emergency|immediate)\s+(alert|warning|notice|action)\b", "Urgency: urgent alert without clear source."),
        (r"\bthis\s+is\s+not\s+a\s+drill\b", "False urgency: 'this is not a drill' is often misinformation."),
        (r"\beveryone\s+(is\s+)?(saying|talking|discussing)\b", "Bandwagon: 'everyone is saying' implies false consensus."),
        (r"\byou\s+won'?t\s+see\s+this\s+(on|in)\s+(mainstream|news|tv|media)\b", "Media distrust: 'suppressed by mainstream media'."),
        (r"\bthey\s+(don'?t|cannot)\s+(handle|deal\s+with|silence)\s+(the\s+)?truth\b", "Persecution complex: 'they can't handle the truth'."),
        (r"\bwake\s+up\s+(sheeple|people|america|india)\b", "Condescension: 'wake up' rhetoric common in conspiracy."),
        (r"\bdo\s+(your\s+own\s+research|the\s+research|the\s+homework)\b", "Anti-expert: 'do your own research' dismissal of experts."),
        (r"\bopen\s+your\s+eyes\b", "Conspiracy: 'open your eyes' implies hidden truth."),
        (r"\bthe\s+truth\s+(about|behind|of)\b", "Conspiracy: 'the truth about' implies hidden information."),
        (r"\bwhat\s+they\s+don'?t\s+(want\s+you|tell\s+you)\b", "Conspiracy: 'what they don't want you to know'."),
        (r"\b(doctors|scientists|experts)\s+(hate|don'?t\s+want|are\s+hiding)\b", "Anti-expert: professional hate/hide claims."),
        (r"\b(secret|hidden|censored)\s+(report|study|research|document|video|footage)\b", "Suppressed content: hidden document trope."),
        (r"\bproven\s+(wrong|false|incorrect|debunked)\b", "Denial: 'proven wrong' dismissal of established facts."),
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
        "outrage", "disgust", "appalled", "shocked", "terrified", "furious",
        "heartbreaking", "devastated", "unbelievable", "incredible", "mind-blowing",
        "jaw-dropping", "unthinkable", "nightmare", "horrifying", "sickening",
        "disgraceful", "appalling", "abomination", "catastrophe", "disaster",
        "horrific", "tragic", "agonizing", "excruciating", "insufferable",
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
            fake_reasons.append("Multiple exclamation marks — hallmark of sensationalist misinformation.")

    all_caps_words = len(re.findall(r"\b[A-Z]{4,}\b", news_text))
    if all_caps_words >= 3:
        fake_score += 1
        if len(fake_reasons) < 3:
            fake_reasons.append("Excessive SHOUTING in all-caps words — common in fake news.")

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

    office_claim = _is_political_office_claim(news_text)
    if prediction == "UNSURE":
        if office_claim:
            prediction = "FAKE"
            confidence = 62.0
            fake_reasons.append(
                "Political-office claim lacking strong verification evidence is treated as FAKE by default."
            )
        else:
            prediction = "REAL"
            confidence = max(58.0, confidence)
            fake_reasons.append(
                "No misinformation signals detected. Insufficient evidence to confirm or deny — treating as potentially real."
            )

    explanation_parts = []
    if prediction == "FAKE":
        if fake_reasons:
            explanation_parts.append("Misinformation signals detected: " + " ".join(fake_reasons[:3]))
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
            reason_parts.append("Rule/evidence contradiction: " + "; ".join(issues[:3]) + ".")
        if llm_exp:
            reason_parts.append("AI reasoning: " + _clean_sentence(llm_exp, 320))
        if fact_note:
            reason_parts.append("External fact-check signal: " + _clean_sentence(fact_note, 320))
        if not reason_parts:
            reason_parts.append(
                "The article contains reliability problems or unverifiable claims that are not supported by the strongest available checks."
            )
    else:
        if fact_note:
            reason_parts.append("External support: " + _clean_sentence(fact_note, 320))
        if trusted_titles:
            reason_parts.append("Trusted-source support: " + " | ".join(trusted_titles[:3]) + ".")
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


def analyze_with_phi3(
    news_text: str,
    display_policy: Optional[str] = None,
    source_type: str = "text",
) -> Dict[str, Any]:
    # Step 1: fetch all external evidence in parallel before LLM call
    fact_check_results = _google_fact_check(news_text)

    # Extract structured claim
    claim = extract_claim(news_text)
    category_info = detect_category(news_text)

    # Knowledge Base Check
    knowledge_result = resolve_knowledge(news_text)

    print("\n========== KNOWLEDGE ==========")
    print(knowledge_result)
    print("===============================\n")

    print("\n========== CLAIM ==========")
    print(claim)
    print("===========================\n")

    # Detect category
    category_info = detect_category(news_text)

    print("\n========== CATEGORY ==========")
    print(category_info)
    print("==============================\n")

    trusted_results = _search_trusted_sources(news_text)

    print("\n========== TRUSTED RESULTS ==========")
    for i, r in enumerate(trusted_results, 1):
        print(f"\nArticle {i}")
        print("Title:", r.get("title"))
        print("Published:", r.get("published"))
        print("Source:", r.get("source"))
        print("Summary:", r.get("summary"))
    print("=====================================\n")

    news_results = (
        _search_news(news_text) if NEWS_API_KEY else _fetch_rss_news(news_text)
    )

    # Step 2: fetch multiple relevant News API articles for context
    news_api_articles = _news_api_fetch_relevant(news_text) if NEWS_API_KEY else []

    category = _classify_category(news_text)

    # NEW FACT CHECKING PIPELINE
    pipeline_result = None

    try:
        claim = extract_claim(news_text)
        print("STEP 1 OK")

        evidence = retrieve_evidence(claim)
        print("STEP 2 OK")

        evidence = filter_evidence(claim, evidence)
        print("STEP 3 OK")

        reasoning = reason_over_evidence(
    claim,
    evidence,
    _call_ollama,
)
        print("STEP 4 OK")

        pipeline_result = combine_verdicts(reasoning)
        print("STEP 5 OK")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Pipeline Error:", e)

    # Build rich context string from top-N articles — passed to Groq for reasoning
    fallback_result = _heuristic_only_analysis(news_text)

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

    print("\n======================")
    print("GROQ RAW RESPONSE")
    print("======================")
    print(groq_raw)
    print("======================\n")

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
- If the text asserts a public office, election result, or government role, verify the claim against current credible facts and official incumbency.
- Use trusted news sources and known public records when available.
- Factual contradictions, role mismatches, conspiracy claims, and manipulative clickbait indicate FAKE.
- Verified facts, ordinary official statements, and measured language indicate REAL.
- If the claim is uncertain or unsupported, prefer FAKE over REAL and keep confidence conservative.
- Your explanation must mention the specific claim in the news text.

News text: "{news_text}"

Respond EXACTLY:
VERDICT: [REAL or FAKE]
CONFIDENCE: [55-99]
EXPLANATION: [1-2 sentences]"""
        )
        if llm_response:
            llm_source = f"Phi-3 (Local LLM)"

    method = fallback_result["method"]
    prediction = fallback_result["prediction"]
    confidence = fallback_result["confidence"]
    llm_verdict = None
    llm_exp = fallback_result["explanation"]
    master_prediction = prediction

    if llm_response:
        llm_verdict = _parse_verdict(llm_response)
        llm_conf = _extract_confidence(llm_response)
        llm_exp = _extract_explanation(llm_response)
        if llm_verdict:
            method = llm_source
            master_prediction = prediction
            print(f"LLM Prediction = {master_prediction}")
        else:
            logger.warning("LLM response lacked a clear verdict; using heuristic fallback prediction")
            prediction = fallback_result["prediction"]
            confidence = fallback_result["confidence"]
            method = fallback_result["method"]

    # MASTER AI VERDICT
    master_prediction = prediction
    master_confidence = confidence
    master_explanation = llm_exp
    policy = (display_policy or os.getenv("DISPLAY_POLICY", "conservative")).lower()

    fact_note = ""
    trusted_note = ""
    high_relevance_trusted = [
        r for r in trusted_results if float(r.get("relevance", 0) or 0) >= 45
    ]
    supported_trusted = []
    contradicted_trusted = []

    for r in high_relevance_trusted:
        title = r.get("title", "")
        summary = r.get("summary", "")
        result = _claim_consistency(news_text, title, summary)
        if result == "SUPPORT":
            supported_trusted.append(r)
        elif result == "CONTRADICT":
            contradicted_trusted.append(r)

    if high_relevance_trusted:
        source_names = ", ".join(
            r.get("source", "trusted source") for r in high_relevance_trusted[:3]
        )
        trusted_note = f"Trusted-source matches from {source_names} were found for this topic."
        if prediction == "REAL":
            confidence = min(98.0, confidence + 5)

    # News API context note
    support_news = []
    if news_api_articles:
        for a in news_api_articles:
            result = _claim_consistency(
                news_text,
                a.get("title", ""),
                a.get("description", "")
            )
            if result == "SUPPORT":
                support_news.append(a)
        best = news_api_articles[0]
        fact_note = (
            f"News API found {len(news_api_articles)} related article(s): "
            f"\"{best['title']}\" from {best['source']} "
            f"({best['published']}, {best['score']}% relevance)."
        )
        if prediction == "REAL" and best["score"] >= 55:
            confidence = min(97.0, confidence + 4)
    elif trusted_note:
        fact_note = trusted_note

    office_claim = _is_political_office_claim(news_text)
    support_news = [a for a in support_news if a.get("score", 0) >= 70]

    strong_support = (
        len(supported_trusted) >= 2 and len(contradicted_trusted) == 0
    ) or (
        len(support_news) >= 2
    )
    contradiction_strength = len(contradicted_trusted)
    support_strength = len(supported_trusted)

    logger.info(f"Support={support_strength}, Contradictions={contradiction_strength}")

    has_stronger_support = False
    recent_trusted_results = []
    try:
        recent_supported = [r for r in supported_trusted if _is_recent(r.get("published", ""), days=30)]
        recent_trusted_results = [
            r for r in (trusted_results or [])
            if _is_recent(r.get("published", ""), days=30) and float(r.get("relevance", 0) or 0) >= 50
        ]
        if len(recent_supported) >= 1 and len(supported_trusted) >= 2:
            has_stronger_support = True
        if len(recent_supported) >= 2 and len(contradicted_trusted) == 0:
            has_stronger_support = True
        for a in support_news:
            try:
                if a.get("score", 0) >= 85 and _is_recent(a.get("published", ""), days=14):
                    has_stronger_support = True
                    break
            except Exception:
                continue
        if fact_check_results:
            for fc in fact_check_results:
                rating = (fc.get("rating") or "").lower()
                if any(k in rating for k in ("true", "correct", "accurate")):
                    has_stronger_support = True
                    break
    except Exception:
        has_stronger_support = strong_support

    # CENTRAL DECISION ENGINE (V2)
    decision = decide_verdict(
        llm_verdict=llm_verdict or prediction,
        llm_confidence=confidence,
        pipeline_result=pipeline_result,
        fact_check_results=fact_check_results,
        supported_trusted=supported_trusted,
        contradicted_trusted=contradicted_trusted,
        knowledge_result=knowledge_result,
    )

    print("\n========== DECISION ENGINE ==========")
    print(decision)
    print("=====================================\n")

    prediction = decision["prediction"]
    master_prediction = prediction
    confidence = decision["confidence"]

    if decision.get("explanation"):
        llm_exp = decision["explanation"]

    logger.info(
        f"has_stronger_support={has_stronger_support} supported_trusted={len(supported_trusted)} "
        f"trusted_results={(len(trusted_results) if trusted_results else 0)} "
        f"recent_trusted_results={len(recent_trusted_results)}"
    )

    # If the semantic pipeline is highly confident, use it.
    if pipeline_result:
        if pipeline_result["verdict"] == "REAL":
            prediction = "REAL"
            master_prediction = "REAL"
            confidence = max(confidence, pipeline_result["confidence"])
        elif pipeline_result["verdict"] == "FAKE":
            prediction = "FAKE"
            master_prediction = "FAKE"
            confidence = max(confidence, pipeline_result["confidence"])

    is_misleading = False
    display_prediction = prediction

    if prediction == "FAKE" and strong_support and policy == "aggressive":
        if office_claim:
            if has_stronger_support:
                is_misleading = True
                display_prediction = "REAL"
                fact_note = fact_note or "Live news or trusted sources strongly support this political office claim."
            else:
                is_misleading = True
                display_prediction = prediction
                fact_note = fact_note or "This political office claim has some supporting context, but requires higher-confidence evidence before changing the verdict."
        else:
            is_misleading = True
            display_prediction = "REAL"
            fact_note = fact_note or "Live news or trusted sources strongly support this claim."
    elif prediction == "FAKE" and strong_support and policy == "conservative":
        is_misleading = True
        display_prediction = prediction

    # Google Fact Check API
    fact_check_truth = False
    if fact_check_results:
        fc_info = "; ".join(
            f"{c['claim'][:70]} - {c['rating']}" for c in fact_check_results[:2]
        )
        findings_lower = " ".join(str(f).lower() for f in fact_check_results)
        if any(kw in findings_lower for kw in ["false", "misleading", "fake", "incorrect", "hoax"]):
            master_prediction = "FAKE"
            prediction = "FAKE"
            confidence = min(99.0, confidence + 8)
            fact_note = f"External fact-check evidence flags it: {fc_info}."
        elif any(kw in findings_lower for kw in ["true", "correct", "accurate", "factual"]):
            master_prediction = "REAL"
            prediction = "REAL"
            confidence = min(99.0, confidence + 8)
            fact_note = f"External fact-check evidence supports it: {fc_info}."
            fact_check_truth = True

    if prediction == "REAL" and fallback_result["prediction"] == "FAKE":
        no_strong_evidence = (
            not has_stronger_support
            and not high_relevance_trusted
            and not support_news
            and not fact_check_truth
        )
        if no_strong_evidence and master_prediction != "REAL":
            prediction = "FAKE"
            display_prediction = "FAKE"
            confidence = max(60.0, min(confidence, fallback_result["confidence"]))
            fact_note = (
                (fact_note + " ") if fact_note else ""
            ) + "Local heuristic analysis found misleading patterns and no strong trusted evidence justified a REAL verdict."

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
        all_fact_checks.append({
            "claim": t["title"],
            "rating": f"Trusted source match ({t.get('relevance', 0)}%)",
            "source": t["source"],
            "url": t.get("url", ""),
            "published": t.get("published", ""),
            "trusted": True,
        })
    for a in (news_results or [])[:2]:
        all_fact_checks.append({
            "claim": a["title"],
            "rating": "Referenced",
            "source": a["source"],
            "url": a.get("url", ""),
            "published": a.get("published", ""),
        })

    if not llm_response and not groq_raw:
        method = fallback_result["method"]

    # Pull structured XAI fields from Groq response when available
    xai_reasons = groq_structured.get("reasons", [])
    xai_suspicious = groq_structured.get("suspicious_phrases", [])
    manipulation_type = groq_structured.get("manipulation_type", "None")

    low_severity_manips = {"Misattribution", "Outdated Info", "Emotional Manipulation", "None"}

    policy = (display_policy or os.getenv("DISPLAY_POLICY", "conservative")).lower()

    if policy == "force_real":
        is_misleading = True if prediction == "FAKE" else False
        display_prediction = "REAL"
    elif policy == "conservative":
        if prediction == "FAKE" and manipulation_type in low_severity_manips and (
            len(trusted_results) > 0 or len(news_api_articles) > 0
        ):
            is_misleading = True
            display_prediction = prediction
    else:
        # aggressive
        if prediction == "FAKE" and manipulation_type in low_severity_manips and (
            len(trusted_results) > 0 or len(news_api_articles) > 0
        ):
            if not has_stronger_support:
                is_misleading = True
                display_prediction = prediction
            else:
                is_misleading = True
                display_prediction = "REAL"

    # Final safety enforcement for political office claims
    try:
        if office_claim and not has_stronger_support and master_prediction != "REAL":
            if prediction != "FAKE":
                prediction = "FAKE"
            display_prediction = "FAKE"
            is_misleading = False
            confidence = max(70.0, float(confidence))
            explanation = (
                "Political-office claim lacking strong trusted evidence; defaulting to FAKE. "
                + (explanation or "")
            )[:1800]
    except Exception:
        pass

    return {
        "prediction": prediction,
        "display_prediction": display_prediction,
        "is_misleading": is_misleading,
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
        "decision_engine_result": decision,
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
                "active_model": PRIMARY_MODEL if primary_ok else (FAST_MODEL if fast_ok else "none"),
                "models": names,
            }
        return {"running": False, "error": "API not responding"}
    except requests.exceptions.ConnectionError:
        return {"running": False, "error": "Ollama not running"}
    except requests.exceptions.Timeout:
        return {"running": False, "error": "Ollama server hung"}
    except Exception as e:
        return {"running": False, "error": str(e)}