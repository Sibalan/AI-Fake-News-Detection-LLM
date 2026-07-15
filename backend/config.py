import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "rvce-mca-project-secret-key-2024")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///"
        + os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "database", "app.db"
        ),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-rvce-mca")
    JWT_ACCESS_TOKEN_EXPIRES = 86400
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "static", "assets"
    )
    MODEL_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ml", "models"
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Real-time news ingestion and verification config
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
    NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")
    MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY", "")
    RSS_FETCH_TIMEOUT = int(os.getenv("RSS_FETCH_TIMEOUT", 10))

    QDRANT_HOST = os.getenv("QDRANT_HOST", "127.0.0.1")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "news_articles")
    # Feature flag to enable/disable Qdrant usage. Default is disabled so app
    # runs without requiring a local Qdrant service or Docker.
    QDRANT_ENABLED = os.getenv("QDRANT_ENABLED", "false").lower() == "true"

    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    INGEST_INTERVAL_MINUTES = int(os.getenv("INGEST_INTERVAL_MINUTES", 5))

    TRUSTED_SOURCES = [
        "Reuters",
        "BBC",
        "Associated Press",
        "The Hindu",
        "Indian Express",
        "NDTV",
        "Times of India",
        "Hindustan Times",
        "ANI",
        "PIB",
        "CNN",
        "The Guardian",
        "Al Jazeera",
        "NPR",
    ]
