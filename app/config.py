from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str  # BOT_TOKEN в .env
    init_data_max_age_sec: int = 3600  # свежесть auth_date из initData
    dev_mode: bool = False  # необ-ть initData для запуска фронта в обычном браузере

    database_url: str = "postgresql+asyncpg://consult:consult@localhost:5432/consult"
    history_limit: int = 40  # сообщений сессии в контекст модели

    # ── Инференс ──
    inference_backend: str = "stub"  # stub | openai_compat
    llm_base_url: str = "http://localhost:1234/v1"  # LM Studio по умолчанию
    llm_api_key: str = "not-needed"  # LM Studio игнорирует; для Yandex FM — реальный
    llm_model: str = "qwen/qwen3.6-35b-a3b"  # имя модели, как её видит сервер
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.6

    class Config:
        env_file = ".env"


settings = Settings()
