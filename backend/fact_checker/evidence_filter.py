import re


def clean(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def filter_evidence(claim, evidence):

    subject = clean(claim["subject"])

    object_text = clean(claim["object"])

    filtered = []

    subject_words = [w for w in subject.split() if len(w) > 2]
    object_words = [w for w in object_text.split() if len(w) > 3]

    for article in evidence:

        combined = clean(
            article.get("title", "") + " " +
            article.get("summary", "")
        )

        subject_matches = 0
        object_matches = 0

        for word in subject_words:
            if word in combined:
                subject_matches += 1

        for word in object_words:
            if word in combined:
                object_matches += 1

        print("\n-----------------------------")
        print(article.get("title"))
        print("Subject matches:", subject_matches)
        print("Object matches :", object_matches)

        # Keep anything mentioning the subject.
        if subject_matches >= 1:
            filtered.append(article)

    return filtered