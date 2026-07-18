import asyncio
from itertools import cycle

from app.inference.base import InferenceBackend

_CANNED = cycle([
    "Понимаю. Расскажите чуть подробнее — когда вы впервые это заметили?",
    "Спасибо, что делитесь. Как это отражается на вашем дне?",
    "Это звучит непросто. Что в такие моменты помогает вам, пусть даже немного?",
])


class StubBackend(InferenceBackend):
    """Имитирует модель: задержка + канированный ответ по кругу."""

    async def generate(self, system_prompt: str, history: list[dict]) -> str:
        await asyncio.sleep(0.8)
        return next(_CANNED)
