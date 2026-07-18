from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.inference.base import InferenceBackend
from app.inference.stub import StubBackend
from app.security import InitDataError, validate_init_data
from app.storage import repo
from app.storage.db import get_db

router = APIRouter(prefix="/api")

# Точка выбора бэкенда инференса (шаг 4: чтение из settings)
inference: InferenceBackend = StubBackend()

SYSTEM_PROMPT_TEMPLATE = (
    "Ты — ассистент психологического сервиса. "
    "Пользователь: {name}, возраст: {age}. Тема обращения: {topic}. "
    "Черновой промпт, содержательная версия — отдельная итерация."
)


def _auth(init_data: str) -> dict:
    """Общая аутентификация: проверенный user из initData."""
    try:
        return validate_init_data(init_data)["user"]
    except InitDataError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None


# ── Профиль ──────────────────────────────────────────────


class ProfileRequest(BaseModel):
    init_data: str
    first_name: str = Field(min_length=2, max_length=128)
    age: int = Field(ge=1, le=120)
    topic: str = Field(min_length=1, max_length=64)


@router.post("/profile")
async def save_profile(req: ProfileRequest, db: AsyncSession = Depends(get_db)) -> dict:
    tg_user = _auth(req.init_data)

    if req.age < 18:
        raise HTTPException(
            status_code=403, detail="Сервис доступен только совершеннолетним."
        )

    user = await repo.get_or_create_user(
        db, tg_user["id"], tg_user.get("first_name", "")
    )
    await repo.update_profile(db, user, req.first_name, req.age, req.topic)
    await db.commit()
    return {"ok": True}


# ── Чат ──────────────────────────────────────────────────


class ChatRequest(BaseModel):
    init_data: str
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    tg_user = _auth(req.init_data)

    user = await repo.get_or_create_user(
        db, tg_user["id"], tg_user.get("first_name", "")
    )
    if user.age is None:
        # Онбординг не пройден — фронт обязан был вызвать /profile
        raise HTTPException(status_code=409, detail="profile required")

    session = await repo.get_or_create_active_session(db, user)
    await repo.add_message(db, session, "user", req.message)

    history = await repo.get_history(db, session, settings.history_limit)
    # Новое сообщение уже в history: add_message выше, flush внутри session

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        name=user.first_name, age=user.age, topic=user.topic
    )
    reply = await inference.generate(system_prompt, history)

    await repo.add_message(db, session, "assistant", reply)
    await db.commit()
    return ChatResponse(reply=reply)


# ── История сообщений ──────────────────────────────────────────────────


class HistoryRequest(BaseModel):
    init_data: str


@router.post("/history")
async def history(req: HistoryRequest, db: AsyncSession = Depends(get_db)) -> dict:
    tg_user = _auth(req.init_data)
    user = await repo.get_or_create_user(
        db, tg_user["id"], tg_user.get("first_name", "")
    )
    if user.age is None:
        raise HTTPException(status_code=409, detail="profile required")

    session = await repo.get_or_create_active_session(db, user)
    messages = await repo.get_history(db, session, settings.history_limit)
    await db.commit()
    return {"messages": messages}


class MeRequest(BaseModel):
    init_data: str


@router.post("/me")
async def me(req: MeRequest, db: AsyncSession = Depends(get_db)) -> dict:
    tg_user = _auth(req.init_data)
    user = await repo.get_or_create_user(
        db, tg_user["id"], tg_user.get("first_name", "")
    )
    await db.commit()
    onboarded = user.age is not None
    return {
        "onboarded": onboarded,
        "first_name": user.first_name,
        "topic": user.topic,
    }


class MeRequest(BaseModel):
    init_data: str
