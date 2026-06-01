from datetime import datetime
from . import db


class NewsHistory(db.Model):
    __tablename__ = "news_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    news_text = db.Column(db.Text, nullable=False)
    prediction = db.Column(db.String(10), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(20), nullable=True)
    sentiment_score = db.Column(db.Float, nullable=True)
    keywords = db.Column(db.Text, nullable=True)
    suspicious_phrases = db.Column(db.Text, nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    processing_time = db.Column(db.Float, nullable=True)
    method = db.Column(db.String(50), default="phi3")
    source_type = db.Column(db.String(20), default="text")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "news_text": self.news_text[:200] + "..."
            if len(self.news_text) > 200
            else self.news_text,
            "news_text_full": self.news_text,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "sentiment": self.sentiment,
            "sentiment_score": self.sentiment_score,
            "keywords": self.keywords.split(",") if self.keywords else [],
            "suspicious_phrases": self.suspicious_phrases.split(",")
            if self.suspicious_phrases
            else [],
            "source_url": self.source_url,
            "processing_time": self.processing_time,
            "method": self.method,
            "source_type": self.source_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Dataset(db.Model):
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    total_samples = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "file_path": self.file_path,
            "total_samples": self.total_samples,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
