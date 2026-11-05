import pytest

from app.validation import (
    InputValidationError,
    OutputValidationError,
    build_characteristics,
    collect_missing_fields,
    validate_llm_output,
    validate_product_input,
)


def test_non_object_input_is_rejected():
    with pytest.raises(InputValidationError):
        validate_product_input([])


def test_empty_product_is_rejected():
    with pytest.raises(InputValidationError):
        validate_product_input({})


def test_missing_fields_are_reported():
    product = validate_product_input({
        "name": "Прибор",
        "manufacturer": "",
        "specs": {
            "питание": "",
        },
        "description": "",
    })

    missing = collect_missing_fields(product)

    assert any(
        "manufacturer" in item
        for item in missing
    )
    assert any(
        "description" in item
        for item in missing
    )
    assert any(
        "питание" in item
        for item in missing
    )


def test_characteristics_are_copied():
    product = validate_product_input({
        "name": "Прибор",
        "manufacturer": "Производитель",
        "specs": {
            "диапазон": "0–1,6 МПа",
            "питание": "",
        },
        "description": "Описание",
    })

    assert build_characteristics(product) == [
        {
            "name": "диапазон",
            "value": "0–1,6 МПа",
        },
        {
            "name": "питание",
            "value": "данных нет",
        },
    ]


def test_unsupported_industrial_claim_is_rejected():
    product = {
        "name": "Манометр DM 02",
        "manufacturer": "Манотомь",
        "description": (
            "Прибор предназначен для измерения "
            "избыточного давления."
        ),
        "specs": {
            "диапазон": "0–1,6 МПа",
        },
    }

    description = (
        "Манометр DM 02 предназначен для измерения "
        "избыточного давления. "
        "Прибор может использоваться "
        "в промышленных системах. "
    )

    description += (
        "Дополнительные сведения следует "
        "уточнить по паспорту. "
    ) * 15

    result = {
        "seo_title": "Манометр DM 02 Манотомь",
        "seo_description": description[:1000],
        "search_queries": [
            "Манометр DM 02",
            "Манометр DM 02 Манотомь",
            "Манометр 0–1,6 МПа",
        ],
        "commercial_block": (
            "Для измерения избыточного давления."
        ),
    }

    with pytest.raises(
        OutputValidationError,
        match="промышлен",
    ):
        validate_llm_output(
            result,
            product,
        )
