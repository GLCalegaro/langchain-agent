import json
import logging
from collections.abc import Callable
from functools import lru_cache, wraps
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, ParamSpec, TypeVar

from langchain.tools import BaseTool, tool
from pydantic import BaseModel, Field

from logging_config import log_context

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent / "data"

P = ParamSpec("P")
R = TypeVar("R")


def _logged_tool(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            started_at = perf_counter()
            with log_context(tool_name=name):
                logger.info("tool_started")
                try:
                    result = function(*args, **kwargs)
                except Exception:
                    logger.exception(
                        "tool_failed",
                        extra={
                            "duration_ms": round(
                                (perf_counter() - started_at) * 1000,
                                2,
                            )
                        },
                    )
                    raise
                logger.info(
                    "tool_completed",
                    extra={
                        "duration_ms": round(
                            (perf_counter() - started_at) * 1000,
                            2,
                        ),
                        "result_status": (
                            result.get("status")
                            if isinstance(result, dict)
                            else "completed"
                        ),
                    },
                )
                return result

        return wrapper

    return decorator


@lru_cache(maxsize=1)
def _catalog() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _orders() -> dict[str, dict[str, Any]]:
    orders: list[dict[str, Any]] = json.loads(
        (DATA_DIR / "orders.json").read_text(encoding="utf-8")
    )
    return {order["order_id"].upper(): order for order in orders}


def _result(
    status: Literal["success", "needs_input", "not_found", "not_eligible", "error"],
    message: str,
    *,
    data: Any = None,
    protocol: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "data": data,
        "protocol": protocol,
    }


class CatalogSearchInput(BaseModel):
    category: str | None = Field(default=None, description="Categoria da peça")
    size: str | None = Field(default=None, description="Tamanho desejado")
    color: str | None = Field(default=None, description="Cor desejada")
    occasion: str | None = Field(default=None, description="Ocasião de uso")
    gender: str | None = Field(default=None, description="Gênero")
    max_price: float | None = Field(
        default=None,
        gt=0,
        description="Preço máximo em reais",
    )


@tool(args_schema=CatalogSearchInput)
@_logged_tool("search_catalog")
def search_catalog(
    category: str | None = None,
    size: str | None = None,
    color: str | None = None,
    occasion: str | None = None,
    gender: str | None = None,
    max_price: float | None = None,
) -> dict[str, Any]:
    """Pesquisa produtos no catálogo fictício da demonstração."""
    filters = [category, size, color, occasion, gender, max_price]
    if not any(value is not None for value in filters):
        return _result(
            "needs_input",
            "Informe ao menos categoria, tamanho, cor, ocasião, gênero ou preço máximo.",
        )

    def matches(product: dict[str, Any]) -> bool:
        if category and category.lower() not in product["category"].lower():
            return False
        if size and size.upper() not in [item.upper() for item in product["sizes"]]:
            return False
        if color and color.lower() not in [
            item.lower() for item in product["colors"]
        ]:
            return False
        if occasion and occasion.lower() not in [
            item.lower() for item in product["occasions"]
        ]:
            return False
        return not (max_price is not None and product["price"] > max_price)

    products = [product for product in _catalog() if matches(product)][:5]
    if not products:
        return _result(
            "not_found",
            "Nenhum item fictício corresponde aos filtros informados.",
            data=[],
        )
    return _result(
        "success",
        f"{len(products)} item(ns) fictício(s) encontrado(s).",
        data=products,
    )


class OutfitInput(BaseModel):
    style: str = Field(min_length=2, description="Estilo preferido")
    occasion: str = Field(min_length=2, description="Ocasião do look")
    climate: str = Field(min_length=2, description="Clima esperado")
    size: str | None = Field(default=None, description="Tamanho")
    gender: str | None = Field(default=None, description="Gênero")
    max_price: float | None = Field(default=None, gt=0)
    preferences: str | None = Field(
        default=None,
        description="Cores, modelagens ou apresentação preferida",
    )


@tool(args_schema=OutfitInput)
@_logged_tool("suggest_outfit")
def suggest_outfit(
    style: str,
    occasion: str,
    climate: str,
    size: str | None = None,
    gender: str | None = None,
    max_price: float | None = None,
    preferences: str | None = None,
) -> dict[str, Any]:
    """Monta um look usando somente itens do catálogo fictício."""
    candidates = [
        product
        for product in _catalog()
        if occasion.lower() in [item.lower() for item in product["occasions"]]
        and (size is None or size.upper() in product["sizes"])
        and (gender is None or gender.lower() == product["gender"].lower())
        and (max_price is None or product["price"] <= max_price)
    ]
    selected = candidates[:3]
    if not selected:
        return _result(
            "not_found",
            "Não há itens fictícios compatíveis com ocasião, tamanho, gênero e preço.",
            data=[],
        )

    return _result(
        "success",
        (
            f"Look fictício para estilo {style}, ocasião {occasion} e clima "
            f"{climate}."
        ),
        data={
            "items": selected,
            "preferences_considered": preferences,
            "total": round(sum(item["price"] for item in selected), 2),
        },
    )


class OrderInput(BaseModel):
    order_id: str = Field(
        min_length=5,
        description="Código do pedido fictício, por exemplo ARY-1001",
    )


@tool(args_schema=OrderInput)
@_logged_tool("get_order_status")
def get_order_status(order_id: str) -> dict[str, Any]:
    """Consulta o status de um pedido fictício."""
    order = _orders().get(order_id.strip().upper())
    if not order:
        return _result(
            "not_found",
            "Pedido fictício não encontrado. Confira o código informado.",
        )
    public_order = {
        key: order[key]
        for key in ("order_id", "status", "expected_delivery", "history")
    }
    return _result("success", "Pedido fictício localizado.", data=public_order)


class DeliveryInput(BaseModel):
    complaint: str = Field(min_length=5, description="Descrição do problema")
    order_id: str | None = Field(
        default=None,
        description="Código do pedido fictício, quando disponível",
    )


@tool(args_schema=DeliveryInput)
@_logged_tool("late_delivery")
def late_delivery(
    complaint: str,
    order_id: str | None = None,
) -> dict[str, Any]:
    """Orienta problemas de entrega usando o pedido fictício informado."""
    if not order_id:
        return _result(
            "needs_input",
            "Solicite o código do pedido para consultar a entrega fictícia.",
        )

    order = _orders().get(order_id.strip().upper())
    if not order:
        return _result(
            "not_found",
            "Pedido fictício não encontrado. Confira o código informado.",
        )

    status = order["status"]
    if status == "delivered":
        guidance = (
            "O pedido consta como entregue. Oriente a conferência com portaria "
            "ou vizinhos e ofereça abertura de atendimento."
        )
    elif status in {"delayed", "in_transit"}:
        guidance = (
            "A entrega está em trânsito ou atrasada. Informe a previsão do "
            "pedido e ofereça acompanhamento."
        )
    else:
        guidance = "Explique o status atual e direcione ao atendimento."

    return _result(
        "success",
        guidance,
        data={
            "order_id": order["order_id"],
            "status": status,
            "expected_delivery": order["expected_delivery"],
            "complaint_classification": "delivery_issue",
        },
    )


class ReturnInput(BaseModel):
    order_id: str = Field(min_length=5)
    item_id: str = Field(min_length=3)
    reason: str = Field(min_length=3)


@tool(args_schema=ReturnInput)
@_logged_tool("start_return")
def start_return(
    order_id: str,
    item_id: str,
    reason: str,
) -> dict[str, Any]:
    """Valida e inicia uma devolução inteiramente fictícia."""
    order = _orders().get(order_id.strip().upper())
    if not order:
        return _result("not_found", "Pedido fictício não encontrado.")
    if item_id.upper() not in [item.upper() for item in order["item_ids"]]:
        return _result("not_found", "Item não encontrado no pedido fictício.")
    if not order["return_eligible"]:
        return _result(
            "not_eligible",
            "O pedido fictício não está elegível para devolução.",
        )

    protocol = f"DEV-{order['order_id'].split('-')[-1]}-{item_id.upper()}"
    return _result(
        "success",
        "Solicitação fictícia de devolução registrada.",
        data={"order_id": order["order_id"], "item_id": item_id, "reason": reason},
        protocol=protocol,
    )


TOOLS: list[BaseTool] = [
    suggest_outfit,
    search_catalog,
    get_order_status,
    late_delivery,
    start_return,
]
TOOLS_BY_NAME: dict[str, BaseTool] = {item.name: item for item in TOOLS}
