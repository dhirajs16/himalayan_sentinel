from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", ROOT / "backend" / ".env"), extra="ignore"
    )
    environment: str = "development"
    database_url: str = "sqlite:///./var/sentinel.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    storage_dir: Path = Path("var/evidence")
    demo_verification: bool = True
    weather_live: bool = False
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    admin_email: str = ""
    admin_password: str = ""
    government_email: str = ""
    government_password: str = ""
    cookie_secure: bool = False


settings = Settings()
if settings.environment != "development" and (
    settings.demo_verification or not settings.cookie_secure
):
    raise RuntimeError(
        "Production requires DEMO_VERIFICATION=false and COOKIE_SECURE=true"
    )
