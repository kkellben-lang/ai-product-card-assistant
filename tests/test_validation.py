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


def test_missing_warranty_statement_is_allowed():
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
        "Манометр DM 02 производства Манотомь "
        "предназначен для измерения избыточного давления. "
        "Диапазон измерений составляет 0–1,6 МПа. "
        "Сведения о гарантии не указаны. "
        "Сведения о комплектации отсутствуют. "
        "Информацию о сертификации необходимо уточнить. "
        "При выборе прибора следует сверить указанные "
        "характеристики с требованиями проекта. "
    )

    description += (
        "Дополнительные сведения, отсутствующие "
        "во входных данных, следует уточнить "
        "по технической документации. "
    ) * 6

    result = {
        "seo_title": "Манометр DM 02 Манотомь",
        "seo_description": description[:1100],
        "search_queries": [
            "Манометр DM 02",
            "Манометр DM 02 Манотомь",
            "Манометр 0–1,6 МПа",
        ],
        "commercial_block": (
            "Предназначен для измерения "
            "избыточного давления."
        ),
    }

    validated = validate_llm_output(
        result,
        product,
    )

    assert validated["seo_title"] == (
        "Манометр DM 02 Манотомь"
    )


def _length_test_product():
    return {
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


def _length_test_result(description):
    return {
        "seo_title": "Манометр DM 02 Манотомь",
        "seo_description": description,
        "search_queries": [
            "Манометр DM 02",
            "Манометр DM 02 Манотомь",
            "Манометр 0–1,6 МПа",
        ],
        "commercial_block": (
            "Предназначен для измерения "
            "избыточного давления."
        ),
    }


def test_short_seo_description_is_safely_extended():
    description = (
        "Манометр DM 02 предназначен для измерения "
        "избыточного давления. "
    ) * 8

    result = validate_llm_output(
        _length_test_result(description),
        _length_test_product(),
    )

    assert 800 <= len(result["seo_description"]) <= 1200


def test_long_seo_description_is_trimmed():
    description = (
        "Манометр DM 02 предназначен для измерения "
        "избыточного давления. "
    ) * 25

    result = validate_llm_output(
        _length_test_result(description),
        _length_test_product(),
    )

    assert 800 <= len(result["seo_description"]) <= 1200
