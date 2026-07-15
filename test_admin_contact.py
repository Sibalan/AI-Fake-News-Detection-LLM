import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import app as app_module
from models import db
from models.user import User
from models.news import NewsHistory


class AdminContactFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = app_module.create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            admin = User(
                username="admin",
                email="admin@test.com",
                full_name="Admin User",
                is_admin=True,
                is_active=True,
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    def test_contact_message_is_saved_and_visible_to_admin(self):
        response = self.client.post(
            "/contact",
            data={
                "name": "Jane Doe",
                "email": "jane@example.com",
                "message": "Hello admin, I need help with the website.",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Message sent", response.get_data(as_text=True))

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["is_admin"] = True
            sess["username"] = "admin"
            sess["email"] = "admin@test.com"
            sess["full_name"] = "Admin User"

        admin_response = self.client.get("/api/admin/contact-messages")
        self.assertEqual(admin_response.status_code, 200)
        payload = admin_response.get_json()
        self.assertEqual(payload["total_unread"], 1)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["name"], "Jane Doe")

    def test_admin_portal_and_dashboard_analytics_are_available(self):
        with self.app.app_context():
            db.session.add(
                NewsHistory(
                    user_id=1,
                    news_text="A major policy change boosted public trust.",
                    prediction="REAL",
                    confidence=0.92,
                    explanation="Trusted evidence supported the claim.",
                    source_type="text",
                    keywords="policy, trust, government",
                )
            )
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["is_admin"] = True
            sess["username"] = "admin"
            sess["email"] = "admin@test.com"
            sess["full_name"] = "Admin User"

        portal_response = self.client.get("/admin-pannel")
        self.assertEqual(portal_response.status_code, 200)
        self.assertIn(b"Admin Analytics Portal", portal_response.get_data(as_text=True))

        dashboard_response = self.client.get("/api/admin/dashboard")
        self.assertEqual(dashboard_response.status_code, 200)
        payload = dashboard_response.get_json()
        self.assertEqual(payload["admin_count"], 1)
        self.assertIn("top_keywords", payload)
        self.assertIn("source_type_breakdown", payload)


if __name__ == "__main__":
    unittest.main()
