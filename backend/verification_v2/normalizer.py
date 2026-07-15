from typing import Dict


def normalize_article(article: Dict) -> Dict:
    """
    Convert NewsAPI, GNews, NewsData and RSS articles
    into one common format.
    """

    normalized = {
        "title": "",
        "summary": "",
        "content": "",
        "source": "",
        "url": "",
        "published": "",
    }

    normalized["title"] = article.get("title", "")

    normalized["summary"] = (
        article.get("description")
        or article.get("summary")
        or ""
    )

    normalized["content"] = article.get("content", "")

    # URL
    normalized["url"] = (
        article.get("url")
        or article.get("link")
        or ""
    )

    # Source
    source = article.get("source", "")

    if isinstance(source, dict):
        normalized["source"] = source.get("name", "")
    else:
        normalized["source"] = (
            source
            or article.get("source_id", "")
        )

    # Published date
    normalized["published"] = (
        article.get("publishedAt")
        or article.get("pubDate")
        or ""
    )

    return normalized