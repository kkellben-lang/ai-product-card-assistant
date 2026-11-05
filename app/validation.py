import json
import re
from typing import Any


NUMBER_RE = re.compile(
    r"(?<![A-Za-zА-Яа-яЁё])\d+(?:[.,]\d+)?(?![A-Za-zА-Яа-яЁё])"
)

UNSUPPORTED_CLAIM_PATTERNS = (
    (
        re.compile(r"\bпромышлен\w*", re.IGNORECASE),
        "промышленное применение",
    ),
    (
        re.compile(r"\bпредприяти\w*", re.IGNORECASE),
        "применение на предприятиях",
    ),
    (
        re.compile(r"\bпроизводственн\w*", re.IGNORECASE),
        "производственная среда",
    ),
    (
        re.compile(r"\bтрубопровод\w*", re.IGNORECASE),
        "применение в трубопроводах",
    ),
    (
        re.compile(r"\bкотельн\w*", re.IGNORECASE),
        "применение в котельных",
    ),
    (
        re.compile(r"\bжкх\b", re.IGNORECASE),
        "применение в ЖКХ",
    ),
    (
        re.compile(r"\bнад[её]жн\w*", re.IGNORECASE),
        "надёжность",
    ),
    (
        re.compile(r"\bдолговечн\w*", re.IGNORECASE),
        "долговечность",
    ),
    (
        re.compile(r"\bсертифик\w*", re.IGNORECASE),
        "сертификация",
    ),
    (
        re.compile(r"\bгаранти\w*", re.IGNORECASE),
        "гарантия",
    ),
    (
        re.compile(r"\bсрок\s+службы\b", re.IGNORECASE),
        "срок службы",
    ),
    (
        re.compile(r"\bматериал(?:\s+корпуса)?\b", re.IGNORECASE),
        "материал",
    ),
    (
        re.compile(
            r"\bстепен\w*\s+защит\w*",
            re.IGNORECASE,
        ),
        "степень защиты",
    ),
    (
        re.compile(r"\bтемператур\w*", re.IGNORECASE),
        "температурные параметры",
    ),
    (
        re.compile(r"\bкомплектац\w*", re.IGNORECASE),
        "комплектация",
    ),
    (
        re.compile(r"\bсовместим\w*", re.IGNORECASE),
        "совместимость",
    ),
    (
        re.compile(
            r"\bстрана\s+производства\b",
            re.IGNORECASE,
        ),
        "страна производства",
    ),
)


class InputValidationError(ValueError):
    pass


class OutputValidationError(ValueError):
    pass


def validate_product_input(data: Any) -> dict:
    if not isinstance(data, dict):
        raise InputValidationError(
            "Входные данные должны быть JSON-объектом."
        )

    normalized = {}

    for field in ("name", "manufacturer", "description"):
        value = data.get(field, "")

        if value is None:
            value = ""

        if not isinstance(value, str):
            raise InputValidationError(
                f'Поле "{field}" должно быть строкой.'
            )

        normalized[field] = value.strip()

    specs = data.get("specs", {})

    if specs is None:
        specs = {}

    if not isinstance(specs, dict):
        raise InputValidationError(
            'Поле "specs" должно быть JSON-объектом.'
        )

    normalized_specs = {}

    for key, value in specs.items():
        if not isinstance(key, str):
            raise InputValidationError(
                "Названия характеристик должны быть строками."
            )

        if value is None:
            value = ""

        if not isinstance(value, (str, int, float, bool)):
            raise InputValidationError(
                f'Значение характеристики "{key}" '
                "должно быть простым значением."
            )

        normalized_specs[key.strip()] = str(value).strip()

    normalized["specs"] = normalized_specs

    if not any((
        normalized["name"],
        normalized["manufacturer"],
        normalized["description"],
        normalized["specs"],
    )):
        raise InputValidationError(
            "Передан пустой товар: заполните хотя бы одно поле."
        )

    return normalized


def collect_missing_fields(product: dict) -> list[str]:
    """Report explicit gaps and clearly weak input without inventing fields."""
    missing: list[str] = []

    if not product.get("name"):
        missing.append("name — название товара")

    if not product.get("manufacturer"):
        missing.append("manufacturer — производитель")

    description = product.get("description", "").strip()

    if not description:
        missing.append(
            "description — описание/фрагмент технического "
            "паспорта отсутствует"
        )
    elif len(description) < 100 or len(description.split()) < 12:
        missing.append(
            "description — исходное описание слишком краткое; "
            "желательно добавить более полный фрагмент паспорта"
        )

    specs = product.get("specs", {})

    if not specs:
        missing.append(
            "specs — ключевые технические характеристики отсутствуют"
        )
    else:
        for key, value in specs.items():
            if not str(value).strip():
                missing.append(
                    f"specs.{key} — значение отсутствует"
                )

    return missing


def build_characteristics(product: dict) -> list[dict[str, str]]:
    specs = product.get("specs", {})

    if not specs:
        return [{
            "name": "характеристики",
            "value": "данных нет",
        }]

    return [
        {
            "name": key,
            "value": (
                value
                if str(value).strip()
                else "данных нет"
            ),
        }
        for key, value in specs.items()
    ]


def _numbers(text: str) -> set[str]:
    return {
        match.group(0).replace(",", ".")
        for match in NUMBER_RE.finditer(text)
    }


def _sentence_around(text: str, position: int) -> str:
    """Return the sentence containing position."""
    separators = ".!?\\n"

    start = -1
    for separator in separators:
        start = max(start, text.rfind(separator, 0, position))

    end_positions = [
        text.find(separator, position)
        for separator in separators
        if text.find(separator, position) != -1
    ]

    end = min(end_positions) if end_positions else len(text)

    return text[start + 1:end].strip().lower()


def _is_missing_data_statement(sentence: str) -> bool:
    """Allow neutral mentions that explicitly say data is absent."""
    markers = (
        "не указан",
        "не указана",
        "не указано",
        "не указаны",
        "не привед",
        "не предостав",
        "отсутств",
        "нет данных",
        "данных нет",
        "неизвест",
        "не извест",
        "требует уточ",
        "требуют уточ",
        "следует уточ",
        "нужно уточ",
        "необходимо уточ",
    )

    return any(marker in sentence for marker in markers)


def _validate_unsupported_claims(
    generated: str,
    source: str,
) -> None:
    """Reject unsupported positive claims, but allow missing-data notices."""

    violations = []

    for pattern, label in UNSUPPORTED_CLAIM_PATTERNS:
        if pattern.search(source):
            continue

        for match in pattern.finditer(generated):
            sentence = _sentence_around(
                generated,
                match.start(),
            )

            if _is_missing_data_statement(sentence):
                continue

            violations.append(label)
            break

    if violations:
        raise OutputValidationError(
            "В тексте появились неподтверждённые сведения: "
            + ", ".join(sorted(set(violations)))
            + "."
        )



SEO_DESCRIPTION_MIN = 800
SEO_DESCRIPTION_MAX = 1200

SAFE_DESCRIPTION_FILLERS = (
    (
        "Дополнительные сведения, отсутствующие во входных данных, "
        "следует уточнить по техническому паспорту или у производителя."
    ),
    (
        "При выборе товара следует сверить переданные характеристики "
        "с требованиями конкретного проекта."
    ),
    (
        "Черновик подготовлен только на основании предоставленных "
        "исходных данных без добавления неподтверждённых характеристик."
    ),
)


def normalize_seo_description(text: str) -> str:
    """Bring SEO description to 800–1200 chars without inventing facts."""
    text = " ".join(text.split()).strip()

    if len(text) > SEO_DESCRIPTION_MAX:
        sentences = re.split(r"(?<=[.!?])\s+", text)

        selected = []

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            candidate = " ".join(selected + [sentence])

            if len(candidate) > SEO_DESCRIPTION_MAX:
                break

            selected.append(sentence)

        if selected:
            text = " ".join(selected)

        if len(text) > SEO_DESCRIPTION_MAX:
            text = text[:SEO_DESCRIPTION_MAX - 1]

            if " " in text:
                text = text.rsplit(" ", 1)[0]

            text = text.rstrip(" ,;:-") + "."

    filler_index = 0

    while len(text) < SEO_DESCRIPTION_MIN:
        filler = SAFE_DESCRIPTION_FILLERS[
            filler_index % len(SAFE_DESCRIPTION_FILLERS)
        ]

        candidate = f"{text} {filler}".strip()

        if len(candidate) <= SEO_DESCRIPTION_MAX:
            text = candidate
        else:
            break

        filler_index += 1

    return text

def validate_llm_output(result: Any, product: dict) -> dict:
    if not isinstance(result, dict):
        raise OutputValidationError(
            "Ответ модели должен быть JSON-объектом."
        )

    required = (
        "seo_title",
        "seo_description",
        "search_queries",
        "commercial_block",
    )

    missing = [
        key for key in required
        if key not in result
    ]

    if missing:
        raise OutputValidationError(
            "В ответе отсутствуют поля: "
            + ", ".join(missing)
        )

    for key in (
        "seo_title",
        "seo_description",
        "commercial_block",
    ):
        if (
            not isinstance(result[key], str)
            or not result[key].strip()
        ):
            raise OutputValidationError(
                f'Поле "{key}" должно быть непустой строкой.'
            )

        result[key] = result[key].strip()

    result["seo_description"] = normalize_seo_description(
        result["seo_description"]
    )

    if len(result["seo_title"]) > 70:
        raise OutputValidationError(
            "SEO-заголовок длиннее 70 символов: "
            f"{len(result['seo_title'])}."
        )

    if "купить" in result["seo_title"].lower():
        raise OutputValidationError(
            "SEO-заголовок не должен автоматически "
            "добавлять слово «купить»."
        )

    description_length = len(
        result["seo_description"]
    )

    if not 800 <= description_length <= 1200:
        raise OutputValidationError(
            "SEO-описание должно содержать "
            "800–1200 символов, "
            f"сейчас {description_length}."
        )

    queries = result["search_queries"]

    if (
        not isinstance(queries, list)
        or not 3 <= len(queries) <= 5
        or not all(
            isinstance(query, str) and query.strip()
            for query in queries
        )
    ):
        raise OutputValidationError(
            "search_queries должен содержать "
            "3–5 непустых строк."
        )

    result["search_queries"] = [
        query.strip()
        for query in queries
    ]

    source_text = json.dumps(
        product,
        ensure_ascii=False,
    )

    generated_text = " ".join([
        result["seo_title"],
        result["seo_description"],
        result["commercial_block"],
        *result["search_queries"],
    ])

    allowed_numbers = _numbers(source_text)
    generated_numbers = _numbers(generated_text)

    unsupported_numbers = sorted(
        generated_numbers - allowed_numbers
    )

    if unsupported_numbers:
        raise OutputValidationError(
            "Модель добавила числовые значения, "
            "которых нет во входных данных: "
            + ", ".join(unsupported_numbers)
        )

    _validate_unsupported_claims(
        generated_text,
        source_text,
    )

    return result


def validate_fact_review(review: Any) -> dict:
    if not isinstance(review, dict):
        raise OutputValidationError(
            "Ответ факт-чекера должен быть JSON-объектом."
        )

    if not isinstance(
        review.get("is_grounded"),
        bool,
    ):
        raise OutputValidationError(
            "Факт-чекер не вернул is_grounded=true/false."
        )

    claims = review.get("unsupported_claims")

    if not isinstance(claims, list):
        raise OutputValidationError(
            "Факт-чекер не вернул список "
            "unsupported_claims."
        )

    for item in claims:
        if not isinstance(item, dict):
            raise OutputValidationError(
                "Элементы unsupported_claims "
                "должны быть объектами."
            )

        if not isinstance(
            item.get("claim", ""),
            str,
        ):
            raise OutputValidationError(
                "Некорректное поле claim у факт-чекера."
            )

        if not isinstance(
            item.get("reason", ""),
            str,
        ):
            raise OutputValidationError(
                "Некорректное поле reason у факт-чекера."
            )

    return review
