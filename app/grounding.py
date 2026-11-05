from __future__ import annotations


def build_fact_registry(product: dict) -> list[dict[str, str]]:
    """Create the only factual source the LLM is allowed to use."""
    facts: list[dict[str, str]] = []

    if product.get("name"):
        facts.append({
            "id": "F1",
            "field": "name",
            "fact": f"Название товара: {product['name']}",
        })

    if product.get("manufacturer"):
        facts.append({
            "id": "F2",
            "field": "manufacturer",
            "fact": f"Производитель: {product['manufacturer']}",
        })

    if product.get("description"):
        facts.append({
            "id": "F3",
            "field": "description",
            "fact": f"Исходное описание: {product['description']}",
        })

    for index, (key, value) in enumerate(
        product.get("specs", {}).items(),
        start=1,
    ):
        if str(value).strip():
            facts.append({
                "id": f"S{index}",
                "field": f"specs.{key}",
                "fact": f"{key}: {value}",
            })

    return facts
