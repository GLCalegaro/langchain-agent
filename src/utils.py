# ruff: noqa: S101
import os
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from functools import lru_cache
from pathlib import Path
from typing import cast

from langchain.chat_models import BaseChatModel, init_chat_model

# Load .env file if it exists
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# def load_llm() -> BaseChatModel:
#     model = cast(
#         "BaseChatModel",
#         init_chat_model(
#             model="gpt-oss:20b",
#             model_provider="ollama",
#             # base_url="http://127.0.0.1:11434",
#             temperature=0.2,
#             configurable_fields="any",
#         ),
#     )

def load_llm() -> BaseChatModel:
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set. "
            "Get a key at https://aistudio.google.com/apikey"
        )
    
    model = cast(
        "BaseChatModel",
        init_chat_model(
            model="google_genai:gemini-2.5-flash",
            model_provider="google_genai",
            api_key=api_key,
            # base_url="http://127.0.0.1:11434",
            temperature=0.2,
            configurable_fields="any",
        ),
    )

    assert hasattr(model, "bind_tools")
    assert hasattr(model, "invoke")
    assert hasattr(model, "with_config")

    return model

class Connection:
    def use(self) -> None:
        print("Ok, estou usando a connection...")

    def open_connection(self) -> None:
        print("Connection Opened")

    def close_connection(self) -> None:
        print("Connection Closed")


@lru_cache
def get_connection() -> Connection:
    return Connection()


@contextmanager
def sync_lifespan() -> Generator[Connection]:
    print("Sync Abri")
    yield get_connection()
    print("Sync Fechei")


@asynccontextmanager
async def async_lifespan() -> AsyncGenerator[Connection]:
    print("Async Abri")
    yield get_connection()
    print("Async Fechei")