from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.inference.base import InferenceBackend
from app.inference.stub import StubBackend
from app.security import InitDataError, validate_init_data

app = FastAPI(title='consult-mvp')

# Бэкенд инференса
inference: InferenceBackend = StubBackend()


_history: dict[int, list[dict]] = {}

SYSTEM_PROMPT_TEMPLATE = (
    "Ты — ассистент психологического сервиса. Пользователь: {name}. "
    "Черновой промпт, содержательная версия — отдельная итерация."
)

class ChatRequest(BaseModel):
    init_data: str
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post('/api/chat', response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        data = validate_init_data(req.init_data)
    except InitDataError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None

    user = data['user']
    user_id: int = user['id']

    history = _history.setdefault(user_id, [])
    history.append({"role": "user", "content": req.message})

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        name=user.get("first_name", "")
    )
    reply = await inference.generate(system_prompt, history)
    history.append({"role": "assistant", "content": reply})

    return ChatResponse(reply=reply)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
