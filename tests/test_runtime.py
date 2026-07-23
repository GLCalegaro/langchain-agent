from typing import Any

import agent_runtime
import pytest
from agent_runtime import AgentRuntime
from langchain_core.messages import HumanMessage
from settings import Settings


class DatabaseFailure(Exception):
    pass


DatabaseFailure.__module__ = "psycopg.errors"


class FailingGraph:
    def invoke(self, *_args: Any, **_kwargs: Any) -> None:
        raise DatabaseFailure


class WorkingGraph:
    def invoke(self, inputs: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        return inputs


class FakeModel:
    def bind_tools(self, _tools: Any) -> "FakeModel":
        return self


def test_runtime_switches_to_memory_after_database_failure(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        agent_runtime,
        "build_graph",
        lambda *_args, **_kwargs: WorkingGraph(),
    )
    runtime = AgentRuntime(
        settings=settings,
        model=FakeModel(),
        graph=FailingGraph(),
        backend="postgres",
    )

    result = runtime.invoke(
        "thread-runtime",
        HumanMessage(content="Teste"),
    )

    assert result["messages"]
    assert runtime.backend == "memory"
    assert runtime.persistence_warning is not None
