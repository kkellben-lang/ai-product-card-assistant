import json
import logging
import os

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from .base import LLMServiceError, ProductCardGenerator
from ..prompts import (
    build_generation_prompt,
    build_review_prompt,
)
from ..validation import (
    OutputValidationError,
    validate_fact_review,
    validate_llm_output,
)


logger = logging.getLogger(__name__)


GENERATION_RESPONSE_FORMAT = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "seo_title": {"type": "string"},
            "seo_description": {"type": "string"},
            "search_queries": {
                "type": "array",
                "items": {"type": "string"},
            },
            "commercial_block": {"type": "string"},
        },
        "required": [
            "seo_title",
            "seo_description",
            "search_queries",
            "commercial_block",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


REVIEW_RESPONSE_FORMAT = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "is_grounded": {
                "type": "boolean",
            },
            "unsupported_claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {
                            "type": "string",
                        },
                        "reason": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "claim",
                        "reason",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "is_grounded",
            "unsupported_claims",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


def _bool(
    value: str | None,
    default: bool = False,
) -> bool:
    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


class GigaChatProductCardGenerator(
    ProductCardGenerator
):
    def __init__(self):
        credentials = os.getenv(
            "GIGACHAT_CREDENTIALS",
            "",
        ).strip()

        if not credentials:
            raise LLMServiceError(
                "Не задан GIGACHAT_CREDENTIALS. "
                "Добавьте Authorization Key в .env."
            )

        self.model = os.getenv(
            "GIGACHAT_MODEL",
            "GigaChat-3-Ultra",
        )

        self.client = GigaChat(
            base_url=os.getenv(
                "GIGACHAT_BASE_URL",
                "https://api.giga.chat/v1",
            ),
            credentials=credentials,
            scope=os.getenv(
                "GIGACHAT_SCOPE",
                "GIGACHAT_API_PERS",
            ),
            verify_ssl_certs=_bool(
                os.getenv("GIGACHAT_VERIFY_SSL"),
                default=False,
            ),
            timeout=float(
                os.getenv(
                    "GIGACHAT_TIMEOUT",
                    "120",
                )
            ),
        )

    def _chat_json(
        self,
        prompt: str,
        response_format: dict,
    ) -> dict:
        chat = Chat(
            model=self.model,
            messages=[
                Messages(
                    role=MessagesRole.USER,
                    content=prompt,
                )
            ],
            response_format=response_format,
            temperature=0.1,
        )

        try:
            response = self.client.chat(chat)

        except Exception as exc:
            raise LLMServiceError(
                "Не удалось выполнить запрос "
                "к GigaChat API. "
                "Проверьте ключ, сеть и настройки доступа."
            ) from exc

        try:
            content = (
                response
                .choices[0]
                .message
                .content
            )

        except (AttributeError, IndexError) as exc:
            raise LLMServiceError(
                "GigaChat API вернул ответ "
                "в неожиданном формате."
            ) from exc

        if not content:
            raise LLMServiceError(
                "GigaChat API вернул пустой ответ."
            )

        try:
            return json.loads(content)

        except json.JSONDecodeError as exc:
            raise OutputValidationError(
                "GigaChat вернул некорректный JSON."
            ) from exc

    def _generate_draft(
        self,
        product: dict,
        correction: str | None = None,
    ) -> dict:
        prompt = build_generation_prompt(
            product,
            correction,
        )

        raw = self._chat_json(
            prompt,
            GENERATION_RESPONSE_FORMAT,
        )

        return validate_llm_output(
            raw,
            product,
        )

    def _review_draft(
        self,
        product: dict,
        draft: dict,
    ) -> dict:
        prompt = build_review_prompt(
            product,
            draft,
        )

        raw = self._chat_json(
            prompt,
            REVIEW_RESPONSE_FORMAT,
        )

        return validate_fact_review(raw)

    @staticmethod
    def _review_correction(
        review: dict,
    ) -> str:
        claims = review.get(
            "unsupported_claims",
            [],
        )

        if not claims:
            return (
                "Факт-чекер не подтвердил черновик. "
                "Используйте ещё более "
                "консервативные формулировки."
            )

        details = []

        for item in claims[:5]:
            claim = item.get(
                "claim",
                "",
            ).strip()

            reason = item.get(
                "reason",
                "",
            ).strip()

            details.append(
                f"«{claim}» — {reason}"
            )

        return (
            "Неподтверждённые утверждения: "
            + "; ".join(details)
        )

    def generate(
        self,
        product: dict,
    ) -> dict:
        correction = None

        for attempt in range(3):
            try:
                draft = self._generate_draft(
                    product,
                    correction,
                )

            except OutputValidationError as exc:
                logger.warning(
                    "Draft %s rejected by "
                    "deterministic validation: %s",
                    attempt + 1,
                    exc,
                )

                if attempt == 2:
                    raise LLMServiceError(
                        "Ответ модели не прошёл "
                        "обязательную проверку. "
                        "Причина указана в терминале."
                    ) from exc

                correction = str(exc)
                continue

            try:
                review = self._review_draft(
                    product,
                    draft,
                )

            except OutputValidationError as exc:
                logger.warning(
                    "Fact reviewer returned invalid "
                    "structured output: %s. "
                    "Using deterministic validation.",
                    exc,
                )

                return draft

            if (
                review["is_grounded"]
                and not review["unsupported_claims"]
            ):
                return draft

            correction = self._review_correction(
                review
            )

            logger.warning(
                "Draft %s rejected by semantic "
                "fact review: %s",
                attempt + 1,
                correction,
            )

        raise LLMServiceError(
            "Не удалось получить подтверждённый "
            "исходными данными текст. "
            "Добавьте более подробные данные о товаре."
        )
