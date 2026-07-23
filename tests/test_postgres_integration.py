import os

import pytest

from checkpointer import build_checkpointer
from settings import Settings


@pytest.mark.integration
def test_postgres_checkpointer_setup() -> None:
    if os.getenv("RUN_POSTGRES_TESTS") != "true":
        pytest.skip("Set RUN_POSTGRES_TESTS=true to run PostgreSQL integration")

    settings = Settings.from_env()
    checkpointer, backend = build_checkpointer(settings)

    assert checkpointer is not None
    assert backend == "postgres"
