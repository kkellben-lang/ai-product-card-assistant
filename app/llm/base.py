from abc import ABC, abstractmethod
class LLMServiceError(RuntimeError):
    pass
class ProductCardGenerator(ABC):
    @abstractmethod
    def generate(self, product: dict) -> dict:
        raise NotImplementedError
