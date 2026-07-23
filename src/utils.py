from typing import Any, cast

from langchain.chat_models import BaseChatModel, init_chat_model

from settings import Settings


def load_llm(settings: Settings | None = None) -> BaseChatModel:
    settings = settings or Settings.from_env()
    if not settings.google_api_key:
        raise ValueError(
            "Configure GOOGLE_API_KEY ou GEMINI_API_KEY para usar o assistente."
        )

    model = cast(
        "BaseChatModel",
        init_chat_model(
            model=f"google_genai:{settings.model_name}",
            model_provider="google_genai",
            api_key=settings.google_api_key,
            temperature=settings.model_temperature,
            max_retries=0,
        ),
    )
    return model


def sanitize_response(response: Any) -> str:
    """Return only displayable text from a model response."""
    if isinstance(response, list):
        text_parts = []
        for item in response:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content = str(item.get("text", "")).strip()
                if text_content:
                    text_parts.append(text_content)
        return "\n".join(text_parts)

    if isinstance(response, dict):
        return str(response.get("text", "")).strip()

    if isinstance(response, str):
        return response.strip()

    return str(response).strip()
