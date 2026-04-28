# app/core/config.py
# ============================================================
# PURPOSE: Saari environment variables ek jagah se manage hoti hain.
# pydantic-settings automatic type validation karta hai aur
# .env file se values read karta hai.
# ============================================================

from pydantic_settings import BaseSettings
from pydantic import AnyUrl


class Settings(BaseSettings):
    # App info
    APP_NAME: str = "Attendance System"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:3000"

    # Database - Supabase PostgreSQL connection string
    DATABASE_URL: str

    # SQLAlchemy connection pool tuning
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        # .env file se automatically values load hogi
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance - poore app mein yahi use hoga
settings = Settings()