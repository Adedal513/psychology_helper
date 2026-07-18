from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import ChatSession, Message, User


async def get_or_create_user(
    db: AsyncSession, tg_user_id: int, first_name: str
) -> User:
    user = await db.scalar(select(User).where(User.tg_user_id == tg_user_id))
    if user is None:
        user = User(tg_user_id=tg_user_id, first_name=first_name)
        db.add(user)
        await db.flush()
    return user


async def update_profile(
    db: AsyncSession, user: User, first_name: str, age: int, topic: str
) -> None:
    user.first_name = first_name
    user.age = age
    user.topic = topic


async def get_or_create_active_session(db: AsyncSession, user: User) -> ChatSession:
    session = await db.scalar(
        select(ChatSession)
        .where(ChatSession.user_id == user.id, ChatSession.status == "active")
        .order_by(ChatSession.started_at.desc())
    )
    if session is None:
        session = ChatSession(user_id=user.id)
        db.add(session)
        await db.flush()
    return session


async def get_history(db: AsyncSession, session: ChatSession, limit: int) -> list[dict]:
    """Последние `limit` сообщений сессии в хронологическом порядке.

    В БД хранится вся история; limit ограничивает только то,
    что уходит в контекст модели.
    """
    rows = await db.scalars(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return [{"role": m.role, "content": m.content} for m in reversed(list(rows))]


async def add_message(
    db: AsyncSession, session: ChatSession, role: str, content: str
) -> None:
    db.add(Message(session_id=session.id, role=role, content=content))
