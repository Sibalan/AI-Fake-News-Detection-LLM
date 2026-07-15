from datetime import datetime, timezone


def parse_date(date_str):
    """
    Parse common news date formats.
    Returns None if parsing fails.
    """

    if not date_str:
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue

    return None


def is_recent(date_str, days=30):
    """
    Returns True if the article is within the last 'days' days.
    """

    article_date = parse_date(date_str)

    if article_date is None:
        return False

    age = datetime.now(timezone.utc) - article_date

    return age.days <= days


def recency_score(date_str):
    """
    Score from 0–100 based on freshness.
    """

    article_date = parse_date(date_str)

    if article_date is None:
        return 20

    age = (datetime.now(timezone.utc) - article_date).days

    if age <= 1:
        return 100

    if age <= 7:
        return 95

    if age <= 30:
        return 85

    if age <= 90:
        return 70

    if age <= 365:
        return 50

    return 25