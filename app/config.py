"""Application configuration loaded from environment variables and ``.env``."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "TravelPilot"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # LLM
    GEMINI_API_KEY: str = Field(default="", repr=False)
    GEMINI_MODEL_SMALL: str = "gemini-3.5-flash-lite"
    GEMINI_MODEL_MEDIUM: str = "gemini-3.7-flash"
    GEMINI_MODEL_LARGE: str = "gemini-3.8-flash"

    # OpenStreetMap / Nominatim
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = "TravelPilot/1.0 (your-email@example.com)"

    # Overpass
    OVERPASS_BASE_URL: str = "https://overpass-api.de/api/interpreter"

    # OSRM
    OSRM_BASE_URL: str = "https://router.project-osrm.org"

    # Open-Meteo
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_TIMEOUT: int = 10
    OPEN_METEO_HISTORICAL_FORECAST_URL: str = (
        "https://historical-forecast-api.open-meteo.com/v1"
    )
    OPEN_METEO_HISTORICAL_FORECAST_TIMEOUT: int = 15

    # Wikipedia / MediaWiki
    WIKIPEDIA_API_URL: str = "https://en.wikipedia.org/w/api.php"

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "travelpilot"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = Field(default="", repr=False)

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # RAG / vector store
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"

    # Application URLs
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:8501"


settings = Settings()