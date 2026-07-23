from tools import (
    get_order_status,
    late_delivery,
    search_catalog,
    start_return,
    suggest_outfit,
)


def test_search_catalog_returns_filtered_products() -> None:
    result = search_catalog.invoke({"category": "camiseta", "size": "M"})

    assert result["status"] == "success"
    assert result["data"][0]["product_id"] == "PRD-101"


def test_search_catalog_requires_a_filter() -> None:
    result = search_catalog.invoke({})

    assert result["status"] == "needs_input"


def test_suggest_outfit_uses_catalog_data() -> None:
    result = suggest_outfit.invoke(
        {
            "style": "casual",
            "occasion": "passeio",
            "climate": "ameno",
            "size": "M",
        }
    )

    assert result["status"] == "success"
    assert result["data"]["items"]


def test_order_status_handles_unknown_order() -> None:
    result = get_order_status.invoke({"order_id": "ARY-9999"})

    assert result["status"] == "not_found"


def test_late_delivery_requests_order_id() -> None:
    result = late_delivery.invoke(
        {"complaint": "Meu pedido ainda não chegou", "order_id": None}
    )

    assert result["status"] == "needs_input"


def test_start_return_creates_deterministic_protocol() -> None:
    result = start_return.invoke(
        {
            "order_id": "ARY-1002",
            "item_id": "PRD-103",
            "reason": "Tamanho incorreto",
        }
    )

    assert result["status"] == "success"
    assert result["protocol"] == "DEV-1002-PRD-103"
