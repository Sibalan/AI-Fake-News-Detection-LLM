from datetime import datetime
from . import db


class LiveArticle(db.Model):
    __tablename__ = "live_articles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    author = db.Column(db.String(200), nullable=True)
    source = db.Column(db.String(200), nullable=False)
    source_domain = db.Column(db.String(200), nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    country = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    keywords = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    article_url = db.Column(db.String(500), nullable=False, unique=True)
    embedding_id = db.Column(db.String(100), nullable=True)
    credibility_score = db.Column(db.Float, nullable=True)
    verification_status = db.Column(db.String(50), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    fact_check_status = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "author": self.author,
            "source": self.source,
            "source_domain": self.source_domain,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "country": self.country,
            "language": self.language,
            "category": self.category,
            "keywords": self.keywords.split(",") if self.keywords else [],
            "image_url": self.image_url,
            "article_url": self.article_url,
            "embedding_id": self.embedding_id,
            "credibility_score": self.credibility_score,
            "verification_status": self.verification_status,
            "summary": self.summary,
            "fact_check_status": self.fact_check_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
