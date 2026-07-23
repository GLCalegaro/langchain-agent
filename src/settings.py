import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def _as_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(name: str, default: int, *, minimum: int = 1) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    value = int(raw_value)
    if value < minimum:
        raise ValueError(f"{name} must be greater than or equal to {minimum}")
    return value


def _as_float(
    name: str,
    default: float,
    *,
    minimum: float = 0.0,
    maximum: float = 2.0,
) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    value = float(raw_value)
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    google_api_key: str | None
    db_dsn: str | None
    model_name: str
    model_temperature: float
    model_max_retries: int
    recursion_limit: int
    max_concurrency: int
    log_level: str
    langsmith_tracing: bool
    langsmith_api_key: str | None
    langsmith_project: str
    environment: str

    @classmethod
    def from_env(cls) -> "Settings":
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be a valid Python logging level")

        return cls(
            google_api_key=os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY"),
            db_dsn=os.getenv("DB_DSN"),
            model_name=os.getenv("MODEL_NAME", "gemini-2.5-flash"),
            model_temperature=_as_float("MODEL_TEMPERATURE", 0.2),
            model_max_retries=_as_int("MODEL_MAX_RETRIES", 2),
            recursion_limit=_as_int("RECURSION_LIMIT", 12, minimum=2),
            max_concurrency=_as_int("MAX_CONCURRENCY", 4),
            log_level=log_level,
            langsmith_tracing=_as_bool(os.getenv("LANGSMITH_TRACING")),
            langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
            langsmith_project=os.getenv("LANGSMITH_PROJECT", "aryaz"),
            environment=os.getenv("APP_ENV", "development"),
        )
