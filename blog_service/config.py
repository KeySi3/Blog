from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс конфигурации приложения.
    """
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "blog_db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
