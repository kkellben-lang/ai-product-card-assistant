from app.grounding import build_fact_registry
from app.validation import collect_missing_fields


def test_fact_registry_contains_only_input_facts():
    product = {
        "name": "Манометр DM 02",
        "manufacturer": "Манотомь",
        "description": "Измеряет избыточное давление.",
        "specs": {
            "диапазон": "0–1,6 МПа",
            "питание": "",
        },
    }

    facts = build_fact_registry(product)
    text = " ".join(item["fact"] for item in facts)

    assert "Манометр DM 02" in text
    assert "Манотомь" in text
    assert "0–1,6 МПа" in text
    assert "промышлен" not in text.lower()
    assert "питание:" not in text.lower()


def test_short_description_is_flagged_for_clarification():
    product = {
        "name": "Манометр DM 02",
        "manufacturer": "Манотомь",
        "description": "Измеряет избыточное давление.",
        "specs": {"диапазон": "0–1,6 МПа"},
    }

    missing = collect_missing_fields(product)
    assert any("слишком краткое" in item for item in missing)
