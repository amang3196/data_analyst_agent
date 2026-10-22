"""App settings, read from environment variables or the .env file.

Every setting has a sensible default except the Gemini API key.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings in one place. Field names match .env keys (case-insensitive)."""

    google_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"  # used if the main model fails

    db_path: str = "data/olist.duckdb"
    notes_path: str = "app/db/olist_notes.md"

    max_attempts: int = 3  # how many SQL tries before the agent gives up
    max_rows: int = 500  # cap on rows returned to the user

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
