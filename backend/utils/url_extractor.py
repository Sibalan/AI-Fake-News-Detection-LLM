import re
import logging
from typing import Dict
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TRUSTED_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "theguardian.com",
    "thehindu.com", "indianexpress.com", "ndtv.com", "timesofindia.indiatimes.com",
    "hindustantimes.com", "economictimes.indiatimes.com", "livemint.com",
    "washingtonpost.com", "nytimes.com", "bloomberg.com", "ft.com",
    "aljazeera.com", "abc.net.au", "cbc.ca", "npr.org", "pbs.org",
    "theatlantic.com", "foreignpolicy.com", "politico.com", "theprint.in",
    "scroll.in", "thewire.in", "indiatoday.in",
}

QUESTIONABLE_DOMAINS = {
    "naturalnews.com", "infowars.com", "beforeitsnews.com", "worldnewsdailyreport.com",
    "empirenews.net", "theonion.com", "clickhole.com", "babylonbee.com",
    "newspunch.com", "yournewswire.com", "neonnettle.com",
}


def check_domain_credibility(url: str) -> Dict:
    """Return a credibility assessment for the given URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    scheme = parsed.scheme.lower()

    https = scheme == "https"
    trusted = any(domain == td or domain.endswith("." + td) for td in TRUSTED_DOMAINS)
    questionable = any(domain == qd or domain.endswith("." + qd) for qd in QUESTIONABLE_DOMAINS)

    score = 50
    if https:
        score += 15
    if trusted:
        score += 35
    if questionable:
        score -= 40
    score = max(0, min(100, score))

    if score >= 80:
        label = "Trusted"
        color = "emerald"
    elif score >= 50:
        label = "Moderately Trusted"
        color = "yellow"
    else:
        label = "Suspicious"
        color = "red"

    return {
        "domain": domain,
        "https": https,
        "score": score,
        "label": label,
        "color": color,
        "trusted_source": trusted,
        "flagged_source": questionable,
    }


def extract_article_from_url(url: str) -> Dict:
    """
    Fetch a URL and extract the article title + body text.
    Returns {"title", "text", "source", "url", "credibility", "error"}.
    """
    result = {
        "title": "",
        "text": "",
        "source": "",
        "url": url,
        "credibility": None,
        "error": None,
    }

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        result["error"] = "Invalid URL — must start with http:// or https://"
        return result

    result["source"] = parsed.netloc.replace("www.", "")
    result["credibility"] = check_domain_credibility(url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except requests.exceptions.Timeout:
        result["error"] = "Request timed out (12s) — the site may be slow or blocked."
        return result
    except requests.exceptions.ConnectionError:
        result["error"] = "Could not connect to the URL. Check the address and try again."
        return result
    except requests.exceptions.HTTPError as e:
        result["error"] = f"HTTP error {e.response.status_code} when fetching the URL."
        return result
    except Exception as e:
        result["error"] = f"Failed to fetch URL: {str(e)[:100]}"
        return result

    # Extract title
    title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if title_match:
        result["title"] = _clean(title_match.group(1))[:250]

    # Try og:title for better title
    og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html, re.IGNORECASE)
    if og_title:
        result["title"] = _clean(og_title.group(1))[:250]

    # Extract body text — strip scripts/styles, then get text from p/article tags
    html_clean = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html_clean = re.sub(r"<style[^>]*>.*?</style>", " ", html_clean, flags=re.DOTALL | re.IGNORECASE)
    html_clean = re.sub(r"<nav[^>]*>.*?</nav>", " ", html_clean, flags=re.DOTALL | re.IGNORECASE)
    html_clean = re.sub(r"<header[^>]*>.*?</header>", " ", html_clean, flags=re.DOTALL | re.IGNORECASE)
    html_clean = re.sub(r"<footer[^>]*>.*?</footer>", " ", html_clean, flags=re.DOTALL | re.IGNORECASE)

    # Prefer <article> or <main> content
    article_match = re.search(r"<article[^>]*>(.*?)</article>", html_clean, re.DOTALL | re.IGNORECASE)
    main_match = re.search(r"<main[^>]*>(.*?)</main>", html_clean, re.DOTALL | re.IGNORECASE)

    source_html = (article_match.group(1) if article_match
                   else main_match.group(1) if main_match
                   else html_clean)

    # Extract all paragraph text
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", source_html, re.DOTALL | re.IGNORECASE)
    text_parts = []
    for p in paragraphs:
        clean = re.sub(r"<[^>]+>", "", p)
        clean = _clean(clean)
        if len(clean) > 30:
            text_parts.append(clean)

    body_text = " ".join(text_parts)

    # Fallback: strip all tags if no paragraphs found
    if len(body_text) < 100:
        body_text = re.sub(r"<[^>]+>", " ", html_clean)
        body_text = _clean(body_text)

    result["text"] = body_text[:5000]

    if not result["text"] and not result["title"]:
        result["error"] = "Could not extract readable content from this page."

    return result


def _clean(s: str) -> str:
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"&lt;", "<", s)
    s = re.sub(r"&gt;", ">", s)
    s = re.sub(r"&quot;", '"', s)
    s = re.sub(r"&#\d+;", " ", s)
    s = re.sub(r"&[a-zA-Z]+;", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()
