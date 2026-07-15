import re
from typing import Dict

CATEGORY_KEYWORDS = {
    "Politics": [
        "prime minister",
        "chief minister",
        "president",
        "governor",
        "minister",
        "parliament",
        "election",
        "mla",
        "mp",
        "government",
        "cabinet",
        "bjp",
        "congress",
        "assembly"
    ],

    "Sports": [
        "ipl",
        "cricket",
        "football",
        "fifa",
        "icc",
        "olympics",
        "world cup",
        "virat kohli",
        "rohit sharma",
        "rcb",
        "csk",
        "match",
        "tournament"
    ],

    "Finance": [
        "rbi",
        "repo rate",
        "stock",
        "share",
        "sensex",
        "nifty",
        "bank",
        "inflation",
        "gdp",
        "budget",
        "economy"
    ],

    "Health": [
        "covid",
        "vaccine",
        "virus",
        "hospital",
        "medicine",
        "doctor",
        "who",
        "disease",
        "health"
    ],

    "Technology": [
        "ai",
        "artificial intelligence",
        "chatgpt",
        "openai",
        "google",
        "microsoft",
        "apple",
        "android",
        "iphone",
        "software"
    ],

    "Science": [
        "nasa",
        "space",
        "moon",
        "mars",
        "isro",
        "rocket",
        "satellite",
        "physics",
        "chemistry",
        "biology"
    ],

    "Education": [
        "ugc",
        "college",
        "school",
        "student",
        "exam",
        "iit",
        "nit",
        "university",
        "education"
    ],

    "Entertainment": [
        "movie",
        "film",
        "actor",
        "actress",
        "director",
        "bollywood",
        "hollywood",
        "music"
    ]
}

def detect_category(text: str) -> Dict:
    """
    Detect the category of the input text.
    Returns:
        {
            "category": "...",
            "confidence": 0-100
        }
    """

    text = text.lower()

    best_category = "General Knowledge"
    best_score = 0

    for category, keywords in CATEGORY_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword.lower() in text:
                score += 1

        if score > best_score:
            best_score = score
            best_category = category

    confidence = min(100, 60 + best_score * 10)

    return {
        "category": best_category,
        "confidence": confidence
    }