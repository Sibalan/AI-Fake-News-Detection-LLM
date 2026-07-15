from verification_v2.pipeline import verify_claim


def main():
    print("=" * 60)
    print("AI Fake News Detector - Verification V2 Test")
    print("=" * 60)

    while True:
        claim = input("\nEnter a claim (or type 'exit'): ").strip()

        if claim.lower() == "exit":
            break

        result = verify_claim(claim)

        print("\n========== RESULT ==========")
        print(f"Prediction : {result['prediction']}")
        print(f"Confidence : {result['confidence']}")
        print(f"Support    : {result['support_count']}")
        print(f"Contradict : {result['contradict_count']}")
        print(f"Irrelevant : {result['irrelevant_count']}")

        print("\nVerified Evidence:")
        for article in result["verified_articles"]:
            print("-" * 40)
            print("Source :", article.get("source"))
            print("Verdict:", article.get("verdict"))
            print("Reason :", article.get("reason"))
            print("URL    :", article.get("url"))

        print("=" * 60)


if __name__ == "__main__":
    main()