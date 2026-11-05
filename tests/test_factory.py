import pytest
from app.llm.base import LLMServiceError
from app.llm.factory import get_generator
from app.llm.mock import MockProductCardGenerator

def test_mock_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER","mock"); assert isinstance(get_generator(),MockProductCardGenerator)
def test_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER","unknown")
    with pytest.raises(LLMServiceError): get_generator()
