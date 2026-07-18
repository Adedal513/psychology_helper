import httpx

from app.config import settings
from app.inference.base import InferenceBackend


class OpenAICompatBackend(InferenceBackend):
    """Клиент к OpenAI-эндпоинту"""

    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url,
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            timeout=httpx.Timeout(60.0, connect=5.0),
        )

    @staticmethod
    def _normalize(system_prompt: str, history: list[dict]) -> list[dict]:
        msgs: list[dict] = []
        # склейка подряд идущих сообщений одной роли (строгие шаблоны
        # требуют чередования user/assistant)
        for m in history:
            if msgs and msgs[-1]["role"] == m["role"]:
                msgs[-1]["content"] += "\n\n" + m["content"]
            else:
                msgs.append(dict(m))
        # окно не должно начинаться с assistant: переносим его в system,
        # чтобы не терять контекст (приветствие, хвост обрезки)
        if msgs and msgs[0]["role"] == "assistant":
            first = msgs.pop(0)
            system_prompt += (
                f"\n\nДиалог уже начат; твоя предыдущая реплика: «{first['content']}»"
            )
        return [{"role": "system", "content": system_prompt}, *msgs]

    async def generate(self, system_prompt: str, history: list[dict]) -> str:
        print(history)
        resp = await self._client.post(
            "/chat/completions",
            json={
                "model": settings.llm_model,
                "messages": self._normalize(system_prompt, history),
                "max_tokens": settings.llm_max_tokens,
                "temperature": settings.llm_temperature,
            },
        )
        if resp.status_code != 200:
            raise RuntimeError(f"LLM error {resp.status_code}: {resp.text}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def aclose(self) -> None:
        await self._client.aclose()
