from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(1000), nullable=False, unique=True)
    image_url = db.Column(db.String(1000), nullable=True)
    source = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(80), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    credibility_score = db.Column(db.Float, nullable=True)
    suspicious_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "image_url": self.image_url,
            "source": self.source,
            "category": self.category,
            "summary": self.summary,
            "credibility_score": self.credibility_score,
            "suspicious_reason": self.suspicious_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
