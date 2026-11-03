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

    # SMS gateway: "android" (SMS Gateway for Android app on a real phone),
    # "africastalking", or "simulator" (no real messages).
    sms_gateway: str = "simulator"
    sms_enabled: bool = False          # older setting: true means Africa's Talking
    sms_number: str = ""               # the number farmers text, shown on the website

    # SMS Gateway for Android (Local Server mode, shown on the app's Home tab)
    android_sms_url: str = ""          # e.g. http://192.168.1.20:8080
    android_sms_username: str = ""
    android_sms_password: str = ""
    android_sms_signing_key: str = ""  # Settings > Webhooks > Signing Key in the app

    # Africa's Talking (SMS and the USSD sandbox)
    at_username: str = "sandbox"
    at_api_key: str = ""
    at_sender_id: str = ""
    ussd_code: str = "*384*211#"

    # Public HTTPS address for gateway callbacks. Leave empty to let the API
    # open a free Cloudflare quick tunnel when it starts.
    public_url: str = ""
    start_tunnel: bool = False

    # Chichewa voice for "Listen": "kasanoma" (fast Piper voice) or "mms" (Meta)
    chichewa_voice: str = "kasanoma"

    # Seeded admin
    admin_phone: str = "0999000000"
    admin_password: str = "admin123"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
