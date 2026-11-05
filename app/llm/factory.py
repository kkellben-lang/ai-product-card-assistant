import os
from .base import LLMServiceError
from .mock import MockProductCardGenerator

def get_generator():
    provider=os.getenv("LLM_PROVIDER","mock").strip().lower()
    if provider=="mock": return MockProductCardGenerator()
    if provider=="gigachat":
        from .gigachat_provider import GigaChatProductCardGenerator
        return GigaChatProductCardGenerator()
    raise LLMServiceError(f'Неизвестный LLM_PROVIDER="{provider}". Используйте "mock" или "gigachat".')

def get_provider_name():
    return os.getenv("LLM_PROVIDER","mock").strip().lower()
