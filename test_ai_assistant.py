import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import app as app_module
from models import db


class AIAssistantTests(unittest.TestCase):
    def setUp(self):
        self.app = app_module.create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def test_assistant_uses_stored_context_for_verdict(self):
        with self.client.session_transaction() as sess:
            sess["assistant_context"] = {
                "article_text": "Scientists found that a new vaccine is 100% safe for everyone.",
                "prediction": "FAKE",
                "confidence": 0.91,
                "explanation": "The claim was unsupported and lacked reliable evidence.",
                "source_type": "text",
            }

        response = self.client.post(
            "/api/assistant/chat",
            json={"message": "Why is this fake?"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["verdict"], "FAKE")
        self.assertIn("Final Verdict", payload["reply"])
        self.assertGreaterEqual(len(payload["history"]), 2)


if __name__ == "__main__":
    unittest.main()
