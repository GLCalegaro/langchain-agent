# ruff: noqa: S101
import os
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from functools import lru_cache
from pathlib import Path
from typing import cast

from langchain.chat_models import BaseChatModel, init_chat_model

# Load .env file if it exists (opcional - para desenvolvimento local)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

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


@asynccontextmanager
async def async_lifespan() -> AsyncGenerator[None]:
    print("Async Abri")
    yield
    print("Async Fechei")


def sanitize_response(response: str | list | dict) -> str:
    """
    Remove metadados sensíveis (tokens, signatures, IDs) da resposta do LLM.
    Garante que apenas texto limpo seja retornado.
    """
    # Se for lista (formato do Google Gemini)
    if isinstance(response, list):
        text_parts = []
        for item in response:
            if isinstance(item, dict) and item.get("type") == "text":
                # Extrai APENAS o campo 'text', descarta 'extras' e outros metadados
                text_content = item.get("text", "").strip()
                if text_content:
                    text_parts.append(text_content)
        return "\n".join(text_parts) if text_parts else ""
    
    # Se for dicionário, tenta extrair o texto
    if isinstance(response, dict):
        return response.get("text", str(response)).strip()
    
    # Se for string, retorna como está
    if isinstance(response, str):
        return response.strip()
    
    # Fallback para qualquer outro tipo
    return str(response).strip()