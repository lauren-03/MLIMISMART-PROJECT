"""Application settings, loaded from the .env file."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "MlimiSmart API"

    # Database
    database_url: str = "mysql+pymysql://root:@localhost:3306/mlimismart"
    allow_sqlite_fallback: bool = True

    # Security
    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # AI: Google Gemini (free key from https://aistudio.google.com/apikey)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # Tried if the main model is retired or unavailable to this key.
    gemini_fallback_model: str = "gemini-flash-latest"

    # SMS
    sms_enabled: bool = False
    at_username: str = "sandbox"
    at_api_key: str = ""
    at_sender_id: str = ""

    # Seeded admin
    admin_phone: str = "0999000000"
    admin_password: str = "admin123"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
