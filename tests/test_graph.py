from collections import deque
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from context import Context
from graph import build_graph
from settings import Settings


class ScriptedModel:
    def __init__(self, responses: list[AIMessage]) -> None:
        self.responses = deque(responses)
        self.calls: list[list[Any]] = []

    def bind_tools(self, _tools: Sequence[BaseTool]) -> "ScriptedModel":
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.calls.append(messages)
        return self.responses.popleft()


def config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def test_direct_response_and_thread_memory(settings: Settings) -> None:
    model = ScriptedModel(
        [AIMessage(content="Primeira"), AIMessage(content="Segunda")]
    )
    graph = build_graph(InMemorySaver(), model=model, settings=settings)

    graph.invoke(
        {"messages": [HumanMessage(content="Olá")]},
        config=config("thread-a"),
        context=Context(),
    )
    result = graph.invoke(
        {"messages": [HumanMessage(content="Continue")]},
        config=config("thread-a"),
        context=Context(),
    )

    assert len(result["messages"]) == 4
    assert model.calls[1][0].type == "system"
    assert sum(message.type == "system" for message in result["messages"]) == 0


def test_threads_are_isolated(settings: Settings) -> None:
    model = ScriptedModel(
        [AIMessage(content="A"), AIMessage(content="B")]
    )
    graph = build_graph(InMemorySaver(), model=model, settings=settings)

    graph.invoke(
        {"messages": [HumanMessage(content="Thread A")]},
        config=config("thread-a"),
        context=Context(),
    )
    result = graph.invoke(
        {"messages": [HumanMessage(content="Thread B")]},
        config=config("thread-b"),
        context=Context(),
    )

    assert len(result["messages"]) == 2
    assert result["messages"][0].content == "Thread B"


def test_state_survives_graph_recompilation(settings: Settings) -> None:
    checkpointer = InMemorySaver()
    first_model = ScriptedModel([AIMessage(content="Persistida")])
    first_graph = build_graph(
        checkpointer,
        model=first_model,
        settings=settings,
    )
    first_graph.invoke(
        {"messages": [HumanMessage(content="Lembre disso")]},
        config=config("thread-resume"),
        context=Context(),
    )

    second_model = ScriptedModel([AIMessage(content="Retomada")])
    second_graph = build_graph(
        checkpointer,
        model=second_model,
        settings=settings,
    )
    snapshot = second_graph.get_state(config("thread-resume"))

    assert snapshot.values["messages"][-1].content == "Persistida"


def test_graph_executes_tool_and_returns_to_model(settings: Settings) -> None:
    model = ScriptedModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_order_status",
                        "args": {"order_id": "ARY-1001"},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="O pedido fictício está atrasado."),
        ]
    )
    graph = build_graph(InMemorySaver(), model=model, settings=settings)

    result = graph.invoke(
        {"messages": [HumanMessage(content="Pedido ARY-1001")]},
        config=config("thread-tools"),
        context=Context(),
    )

    assert result["messages"][-1].content == "O pedido fictício está atrasado."
    assert any(message.type == "tool" for message in result["messages"])


def test_model_retry(settings: Settings) -> None:
    class FlakyModel(ScriptedModel):
        attempts = 0

        def invoke(self, messages: list[Any]) -> AIMessage:
            self.attempts += 1
            if self.attempts == 1:
                raise TimeoutError("temporary")
            return AIMessage(content="Recuperado")

    model = FlakyModel([])
    graph = build_graph(InMemorySaver(), model=model, settings=settings)

    result = graph.invoke(
        {"messages": [HumanMessage(content="Olá")]},
        config=config("thread-retry"),
        context=Context(),
    )

    assert result["messages"][-1].content == "Recuperado"
    assert model.attempts == 2
