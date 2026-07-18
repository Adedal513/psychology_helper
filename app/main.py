from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.storage.db import engine
from app.storage.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Для MVP схема создаётся на старте; при первом изменении
    # существующих таблиц заменяется на Alembic-миграции.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="consult-mvp", lifespan=lifespan)
app.include_router(router)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
