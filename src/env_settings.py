from pydantic import Field, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSeekSettings(BaseSettings):
    api_key: SecretStr
    base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="Базовый URL API DeepSeek",
    )
    model: str = Field(
        default="deepseek-chat",
        description="Название модели DeepSeek",
    )
    max_connections: PositiveInt | None = None
    timeout: PositiveInt = Field(
        default=30,
        description="Таймаут соединения с DeepSeek в секундах",
    )

    model_config = SettingsConfigDict(extra="forbid")


class UnsplashSettings(BaseSettings):
    api_key: SecretStr
    max_connections: PositiveInt
    timeout: PositiveInt = 20

    model_config = SettingsConfigDict(extra="forbid")


class AWSSettings(BaseSettings):
    access_key: SecretStr
    secret_key: SecretStr
    endpoint_url: str
    bucket_name: str

    model_config = SettingsConfigDict(extra="forbid")


class Settings(BaseSettings):
    debug: bool = False
    secret_key: str = "default-secret-key"
    deepseek: DeepSeekSettings | None = None
    unsplash: UnsplashSettings | None = None
    aws: AWSSettings | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="forbid",
    )


settings = Settings()
