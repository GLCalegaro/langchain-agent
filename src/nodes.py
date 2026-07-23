import logging
import time
from collections.abc import Callable, Sequence
from time import perf_counter
from typing import Any, Protocol

from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.runtime import Runtime

from context import Context
from prompts import SYSTEM_PROMPT
from settings import Settings
from state import State
from tools import TOOLS

logger = logging.getLogger(__name__)


def _is_retryable_model_error(error: Exception) -> bool:
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    retryable_names = {
        "APIConnectionError",
        "DeadlineExceeded",
        "RateLimitError",
        "ResourceExhausted",
        "ServiceUnavailable",
    }
    return type(error).__name__ in retryable_names


class ToolBindableModel(Protocol):
    def bind_tools(
        self,
        tools: Sequence[BaseTool],
    ) -> Any: ...


tool_node = ToolNode(
    tools=TOOLS,
    handle_tool_errors=(
        "A ferramenta não conseguiu concluir a operação. Confira os dados "
        "informados ou tente novamente."
    ),
)


def build_call_llm(
    model: ToolBindableModel,
    settings: Settings,
) -> Callable[[State, Runtime[Context]], State]:
    model_with_tools = model.bind_tools(TOOLS)

    def call_llm(state: State, runtime: Runtime[Context]) -> State:
        started_at = perf_counter()
        logger.info(
            "node_started",
            extra={"node": "call_llm", "user_type": runtime.context.user_type},
        )
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]

        last_error: Exception | None = None
        attempts = settings.model_max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                result = model_with_tools.invoke(messages)
                logger.info(
                    "node_completed",
                    extra={
                        "node": "call_llm",
                        "attempt": attempt,
                        "duration_ms": round(
                            (perf_counter() - started_at) * 1000,
                            2,
                        ),
                    },
                )
                return {"messages": [result]}
            except Exception as error:
                last_error = error
                logger.warning(
                    "model_attempt_failed",
                    extra={
                        "node": "call_llm",
                        "attempt": attempt,
                        "error_type": type(error).__name__,
                    },
                )
                if attempt < attempts and _is_retryable_model_error(error):
                    time.sleep(0.25 * (2 ** (attempt - 1)))
                else:
                    break

        logger.error(
            "node_failed",
            extra={
                "node": "call_llm",
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                "error_type": type(last_error).__name__ if last_error else "unknown",
            },
        )
        if last_error is not None:
            raise last_error
        raise RuntimeError("Model invocation failed without an exception")

    return call_llm
