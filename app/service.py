from .llm import get_generator
from .validation import build_characteristics, collect_missing_fields, validate_product_input

def generate_product_card(data: dict) -> dict:
    product=validate_product_input(data)
    generated=get_generator().generate(product)
    return {
        "seo_title":generated["seo_title"],
        "seo_description":generated["seo_description"],
        "key_characteristics":build_characteristics(product),
        "search_queries":generated["search_queries"],
        "commercial_block":generated["commercial_block"],
        "missing_or_unclear_fields":collect_missing_fields(product),
    }
