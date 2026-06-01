from datetime import datetime
from . import db


class PredictionLog(db.Model):
    __tablename__ = "prediction_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    news_text = db.Column(db.Text, nullable=False)
    prediction = db.Column(db.String(10), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50), default="phi3")
    processing_time = db.Column(db.Float)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "news_text": self.news_text[:100],
            "prediction": self.prediction,
            "confidence": self.confidence,
            "method": self.method,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
