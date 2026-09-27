from pydantic import PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSeekSettings(BaseSettings):
    # ВАЖНО: нет значения по умолчанию! Поле строго обязательное, если блок используется.
    api_key: SecretStr
    max_connections: PositiveInt | None = None
    model_config = SettingsConfigDict(extra="forbid")


class UnsplashSettings(BaseSettings):
    # ВАЖНО: нет значения по умолчанию!
    api_key: SecretStr
    max_connections: PositiveInt
    timeout: PositiveInt = 20
    model_config = SettingsConfigDict(extra="forbid")


class Settings(BaseSettings):
    debug: bool = False
    secret_key: str = "default-secret-key"
    deepseek: DeepSeekSettings | None = None
    unsplash: UnsplashSettings | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="forbid",
    )


settings = Settings()
