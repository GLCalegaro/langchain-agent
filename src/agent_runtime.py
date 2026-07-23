import logging
import uuid
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver

from checkpointer import CheckpointBackend, build_checkpointer
from context import Context
from graph import build_graph
from logging_config import log_context
from nodes import ToolBindableModel
from settings import Settings
from utils import load_llm

logger = logging.getLogger(__name__)


def _is_database_error(error: BaseException) -> bool:
    current: BaseException | None = error
    while current is not None:
        module = type(current).__module__
        if module.startswith(("psycopg", "psycopg_pool")):
            return True
        current = current.__cause__ or current.__context__
    return False


@dataclass(slots=True)
class AgentRuntime:
    settings: Settings
    model: ToolBindableModel
    graph: Any
    backend: CheckpointBackend
    persistence_warning: str | None = None

    @classmethod
    def create(cls, settings: Settings) -> "AgentRuntime":
        checkpointer, backend = build_checkpointer(settings)
        model = load_llm(settings)
        graph = build_graph(checkpointer, model=model, settings=settings)
        warning = None
        if backend == "memory":
            warning = (
                "Persistência indisponível: esta conversa existe somente "
                "enquanto o processo estiver ativo."
            )
        return cls(settings, model, graph, backend, warning)

    def _switch_to_memory(self) -> None:
        if self.backend == "memory":
            return
        self.graph = build_graph(
            InMemorySaver(),
            model=self.model,
            settings=self.settings,
        )
        self.backend = "memory"
        self.persistence_warning = (
            "A conexão com o PostgreSQL foi perdida. O atendimento continuou "
            "em memória e novas mensagens não serão persistidas."
        )
        logger.warning(
            "checkpointer_runtime_fallback",
            extra={"backend": "memory", "reason": "postgres_runtime_failure"},
        )

    def config(self, thread_id: str, run_id: uuid.UUID) -> RunnableConfig:
        return RunnableConfig(
            run_id=run_id,
            run_name="aryaz_streamlit",
            tags=["streamlit", self.settings.environment, self.backend],
            metadata={
                "environment": self.settings.environment,
                "checkpoint_backend": self.backend,
            },
            configurable={"thread_id": thread_id},
            max_concurrency=self.settings.max_concurrency,
            recursion_limit=self.settings.recursion_limit,
        )

    def messages(self, thread_id: str) -> list[BaseMessage]:
        run_id = uuid.uuid4()
        config = self.config(thread_id, run_id)
        with log_context(thread_id=thread_id, run_id=str(run_id)):
            try:
                snapshot = self.graph.get_state(config)
            except Exception as error:
                if not _is_database_error(error):
                    raise
                self._switch_to_memory()
                return []
        values = snapshot.values or {}
        return list(values.get("messages", []))

    def invoke(self, thread_id: str, message: BaseMessage) -> dict[str, Any]:
        run_id = uuid.uuid4()
        config = self.config(thread_id, run_id)
        context = Context(user_type="plus")
        started_at = perf_counter()

        with log_context(thread_id=thread_id, run_id=str(run_id)):
            logger.info(
                "agent_run_started",
                extra={"backend": self.backend},
            )
            try:
                result = self.graph.invoke(
                    {"messages": [message]},
                    config=config,
                    context=context,
                )
            except Exception as error:
                if not _is_database_error(error):
                    logger.exception(
                        "agent_run_failed",
                        extra={"backend": self.backend},
                    )
                    raise
                self._switch_to_memory()
                config = self.config(thread_id, run_id)
                result = self.graph.invoke(
                    {"messages": [message]},
                    config=config,
                    context=context,
                )

            logger.info(
                "agent_run_completed",
                extra={
                    "backend": self.backend,
                    "duration_ms": round(
                        (perf_counter() - started_at) * 1000,
                        2,
                    ),
                },
            )
            return result
