import json
import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

_thread_id: ContextVar[str | None] = ContextVar("thread_id", default=None)
_run_id: ContextVar[str | None] = ContextVar("run_id", default=None)
_tool_name: ContextVar[str | None] = ContextVar("tool_name", default=None)

_STANDARD_FIELDS = set(logging.makeLogRecord({}).__dict__)
_RESERVED_FIELDS = _STANDARD_FIELDS | {"message", "asctime"}


def mask_identifier(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        correlation = {
            "thread_id": mask_identifier(_thread_id.get()),
            "run_id": mask_identifier(_run_id.get()),
            "tool": _tool_name.get(),
        }
        payload.update({key: value for key, value in correlation.items() if value})

        for key, value in record.__dict__.items():
            if key not in _RESERVED_FIELDS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["error_type"] = record.exc_info[0].__name__

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


@contextmanager
def log_context(
    *,
    thread_id: str | None = None,
    run_id: str | None = None,
    tool_name: str | None = None,
) -> Iterator[None]:
    tokens = []
    if thread_id is not None:
        tokens.append((_thread_id, _thread_id.set(thread_id)))
    if run_id is not None:
        tokens.append((_run_id, _run_id.set(run_id)))
    if tool_name is not None:
        tokens.append((_tool_name, _tool_name.set(tool_name)))
    try:
        yield
    finally:
        for variable, token in reversed(tokens):
            variable.reset(token)
