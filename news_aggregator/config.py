import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///news_aggregator.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
    GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b")
    GROQ_API_URL = os.getenv(
        "GROQ_API_URL", "https://api.groq.ai/v1/models"
    )
