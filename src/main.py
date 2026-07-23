import logging
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from agent_runtime import AgentRuntime
from logging_config import configure_logging
from settings import Settings
from utils import sanitize_response

logger = logging.getLogger(__name__)
console = Console()


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    runtime = AgentRuntime.create(settings)
    thread_id = str(uuid.uuid4())

    console.print(f"[dim]Conversa: {thread_id} | memória: {runtime.backend}[/dim]")
    while True:
        user_input = Prompt.ask("[bold cyan]Você")
        if user_input.lower() in {"q", "quit", "sair"}:
            break

        try:
            result = runtime.invoke(thread_id, HumanMessage(content=user_input))
        except Exception:
            logger.exception("terminal_agent_failed")
            console.print("[red]Não foi possível concluir a solicitação.[/red]")
            continue

        last_message = result["messages"][-1]
        if isinstance(last_message, AIMessage):
            console.print(Markdown(sanitize_response(last_message.content)))


if __name__ == "__main__":
    main()
