from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ReqioIQ"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api"
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
