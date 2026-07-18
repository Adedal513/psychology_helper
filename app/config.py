from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    init_data_max_age_sec: int = 3600
    dev_mode: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
