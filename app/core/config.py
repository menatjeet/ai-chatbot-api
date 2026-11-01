from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "AI Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = False

    gemini_api_key: str | None = None
    database_url: str | None = None
    jwt_secret_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True
    )


settings = Settings()