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
