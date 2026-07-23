from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.prebuilt.tool_node import tools_condition

from context import Context
from nodes import ToolBindableModel, build_call_llm, tool_node
from settings import Settings
from state import State
from utils import load_llm


def build_graph(
    checkpointer: BaseCheckpointSaver,
    model: ToolBindableModel | None = None,
    settings: Settings | None = None,
) -> CompiledStateGraph[State, Context, State, State]:
    settings = settings or Settings.from_env()
    model = model or load_llm(settings)

    builder = StateGraph(
        state_schema=State,
        context_schema=Context,
        input_schema=State,
        output_schema=State,
    )

    builder.add_node("call_llm", build_call_llm(model, settings))
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "call_llm")
    builder.add_conditional_edges("call_llm", tools_condition, ["tools", END])
    builder.add_edge("tools", "call_llm")

    return builder.compile(checkpointer=checkpointer)
