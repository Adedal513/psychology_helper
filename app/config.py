from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str  # BOT_TOKEN в .env
    init_data_max_age_sec: int = 3600  # свежесть auth_date из initData
    dev_mode: bool = False  # необ-ть initData для запуска фронта в обычном браузере

    database_url: str = "postgresql+asyncpg://consult:consult@localhost:5432/consult"
    history_limit: int = 40  # сообщений сессии в контекст модели

    class Config:
        env_file = ".env"


settings = Settings()
