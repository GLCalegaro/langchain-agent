import logging
from typing import Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from settings import Settings

CheckpointBackend = Literal["postgres", "memory"]

logger = logging.getLogger(__name__)


def build_checkpointer(
    settings: Settings,
) -> tuple[BaseCheckpointSaver, CheckpointBackend]:
    if not settings.db_dsn:
        logger.warning(
            "checkpointer_fallback",
            extra={"backend": "memory", "reason": "DB_DSN_not_configured"},
        )
        return InMemorySaver(), "memory"

    pool = None
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        pool = ConnectionPool(
            conninfo=settings.db_dsn,
            min_size=1,
            max_size=settings.max_concurrency,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
            open=True,
        )
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
        logger.info("checkpointer_ready", extra={"backend": "postgres"})
        return checkpointer, "postgres"
    except Exception:
        if pool is not None:
            pool.close()
        logger.exception(
            "checkpointer_fallback",
            extra={"backend": "memory", "reason": "postgres_unavailable"},
        )
        return InMemorySaver(), "memory"
