from langgraph.prebuilt.tool_node import ToolNode
from langgraph.runtime import Runtime
from langgraph.graph.state import RunnableConfig

from state import State
from tools import TOOLS
from utils import load_llm

tool_node = ToolNode(tools=TOOLS)


def call_llm(state: State, config: RunnableConfig) -> State:
    print("> call llm")
    user_type = config.get("configurable", {}).get("user_type")
    model_provider = "google_genai" if user_type == "plus" else "google_genai"  # noqa: RUF034
    model = "gemini-2.5-flash" if user_type == "plus" else "gemini-2.5-flash"

    llm_with_tools = load_llm().bind_tools(TOOLS)
    llm_with_config = llm_with_tools.with_config(
        config={
            "configurable": {
                "model": model,
                "model_provider": model_provider,
            }
        }
    )

    result = llm_with_config.invoke(
        state["messages"],
    )

    return {"messages": [result]}