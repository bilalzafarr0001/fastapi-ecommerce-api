"""
Application settings.

Every value is read from environment variables or from the `.env` file.
pydantic-settings validates them when the app starts, so a bad config
(for example a missing SECRET_KEY) stops the app right away with a clear
error instead of failing later at runtime.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "ShopSphere API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/shopsphere"
    DB_ECHO: bool = False  # True = print every SQL query in the console (great for learning)

    # --- Security / JWT ---
    SECRET_KEY: str = Field(min_length=32)  # required, no default on purpose
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS (which frontends may call this API from a browser) ---
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- File uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_IMAGE_SIZE_MB: int = 2


# One shared settings object, import it anywhere: `from app.core.config import settings`
settings = Settings()
