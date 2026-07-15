CATEGORY_SOURCES = {

    "politics": [
        "Reuters",
        "PTI",
        "The Hindu",
        "Indian Express",
        "BBC",
        "PIB"
    ],

    "sports": [
        "ESPN",
        "ICC",
        "FIFA",
        "Reuters",
        "PTI"
    ],

    "technology": [
        "TechCrunch",
        "The Verge",
        "Ars Technica",
        "Reuters"
    ],

    "international": [
        "Reuters",
        "BBC",
        "AP News",
        "UN News"
    ],

    "business": [
        "Reuters",
        "Bloomberg",
        "CNBC",
        "Economic Times"
    ],

    "science": [
        "Nature",
        "Science Daily",
        "NASA",
        "ISRO"
    ],

    "health": [
        "WHO",
        "CDC",
        "Reuters",
        "NIH"
    ],

    "crime": [
        "Reuters",
        "PTI",
        "BBC"
    ],

    "entertainment": [
        "Variety",
        "Hollywood Reporter",
        "Reuters"
    ],

    "general": [
        "Reuters",
        "BBC",
        "AP News",
        "PTI",
        "The Hindu"
    ]
}


def get_sources(category: str):

    category = (category or "general").lower()

    return CATEGORY_SOURCES.get(
        category,
        CATEGORY_SOURCES["general"]
    )