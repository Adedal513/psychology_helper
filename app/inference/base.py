from abc import ABC, abstractmethod


class InferenceBackend(ABC):
    """Интерфейс взаимодействия с LLM-инференсом"""

    @abstractmethod
    async def generate(self, system_prompt: str, history: list[dict]) -> str:
        raise NotImplementedError("Implement first.")
