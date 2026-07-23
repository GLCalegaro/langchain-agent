import pytest

from settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        google_api_key="test-key",
        db_dsn=None,
        model_name="test-model",
        model_temperature=0.0,
        model_max_retries=1,
        recursion_limit=8,
        max_concurrency=2,
        log_level="INFO",
        langsmith_tracing=False,
        langsmith_api_key=None,
        langsmith_project="aryaz-tests",
        environment="test",
    )
