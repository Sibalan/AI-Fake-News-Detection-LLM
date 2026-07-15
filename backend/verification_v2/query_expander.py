from typing import List

ALIASES = {

    # Countries
    "usa": [
        "USA",
        "United States",
        "United States of America",
    ],

    "uk": [
        "UK",
        "United Kingdom",
        "Britain",
    ],

    "uae": [
        "UAE",
        "United Arab Emirates",
    ],

    # Politics
    "pm": [
        "Prime Minister",
    ],

    "cm": [
        "Chief Minister",
    ],

    "president": [
        "President",
    ],

    # Sports
    "rcb": [
        "RCB",
        "Royal Challengers Bengaluru",
    ],

    "csk": [
        "CSK",
        "Chennai Super Kings",
    ],

    "mi": [
        "Mumbai Indians",
    ],

    # Technology
    "ai": [
        "Artificial Intelligence",
    ],

    "llm": [
        "Large Language Model",
    ],
}


def expand_queries(queries: List[str]) -> List[str]:

    expanded = list(queries)

    for query in queries:

        lower = query.lower()

        for key, values in ALIASES.items():

            if key in lower:

                for value in values:

                    expanded.append(
                        query.replace(key, value)
                    )

    expanded = list(dict.fromkeys(expanded))

    return expanded