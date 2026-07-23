from dataclasses import replace

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from checkpointer import build_checkpointer
from settings import Settings


def test_missing_dsn_uses_memory(settings: Settings) -> None:
    checkpointer, backend = build_checkpointer(settings)

    assert isinstance(checkpointer, InMemorySaver)
    assert backend == "memory"


def test_connection_failure_uses_memory(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import psycopg_pool

    def fail_to_connect(*_args: object, **_kwargs: object) -> None:
        raise OSError("database unavailable")

    monkeypatch.setattr(psycopg_pool, "ConnectionPool", fail_to_connect)
    configured_settings = replace(
        settings,
        db_dsn="postgresql://example.invalid/aryaz",
    )

    checkpointer, backend = build_checkpointer(configured_settings)

    assert isinstance(checkpointer, InMemorySaver)
    assert backend == "memory"
