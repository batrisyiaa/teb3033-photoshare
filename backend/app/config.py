"""Application settings, read from environment variables (.env file in development)."""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _database_url():
    url = os.getenv("DATABASE_URL", "sqlite:///photoshare.db")
    # Some providers give "postgres://", which SQLAlchemy no longer accepts.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-in-production-0000")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me-in-production-00")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_HOURS", "12")))

    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Connection pool: each Gunicorn worker keeps its own pool of DB connections.
    # pool_pre_ping drops dead connections (e.g. after RDS restarts).
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    if not SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS.update({"pool_size": 5, "max_overflow": 10})

    # Photo storage: "s3" in the cloud, "local" for development on a laptop.
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
    S3_URL_EXPIRY_SECONDS = int(os.getenv("S3_URL_EXPIRY_SECONDS", "3600"))
    LOCAL_UPLOAD_DIR = os.getenv(
        "LOCAL_UPLOAD_DIR",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"),
    )

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
