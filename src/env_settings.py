from typing import Literal

from pydantic import AnyHttpUrl, Field, PositiveFloat, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeepSeekSettings(BaseSettings):
    api_key: SecretStr
    base_url: AnyHttpUrl = Field(
        default="https://api.deepseek.com/v1",
        description="Базовый URL API DeepSeek",
    )
    model: str = Field(
        default="deepseek-chat",
        description="Название модели DeepSeek",
    )
    max_connections: PositiveInt = 5
    timeout: PositiveInt = Field(
        default=30,
        description="Таймаут соединения с DeepSeek в секундах",
    )

    model_config = SettingsConfigDict(extra="forbid")


class UnsplashSettings(BaseSettings):
    api_key: SecretStr
    max_connections: PositiveInt = 5
    timeout: PositiveInt = 20

    model_config = SettingsConfigDict(extra="forbid")


class AWSSettings(BaseSettings):
    access_key: SecretStr
    secret_key: SecretStr
    endpoint_url: AnyHttpUrl
    bucket_name: str
    connect_timeout: PositiveInt = 5
    read_timeout: PositiveInt = 30
    max_connections: PositiveInt = 10

    model_config = SettingsConfigDict(extra="forbid")


class GotenbergSettings(BaseSettings):
    api_url: AnyHttpUrl
    screenshot_width: PositiveInt = 1280
    image_format: Literal["png", "jpeg", "webp"] = "png"
    max_connections: PositiveInt = 5
    timeout: PositiveInt = 10
    wait_delay: PositiveFloat = 8

    model_config = SettingsConfigDict(extra="forbid")


class Settings(BaseSettings):
    debug: bool = False
    deepseek: DeepSeekSettings
    unsplash: UnsplashSettings
    aws: AWSSettings
    gotenberg: GotenbergSettings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="forbid",
    )


settings = Settings()
