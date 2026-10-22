from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

SiteTitle = Annotated[
    str,
    Field(min_length=1, max_length=100, description="Название сайта"),
]


class SiteCreateRequest(BaseModel):
    title: SiteTitle = Field(default="Мой новый сайт", description="Название сайта")
    prompt: str = Field(description="Промпт для генерации сайта")


class SiteDetailResponse(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True)

    id: int = Field(description="ID сайта")
    title: str = Field(description="Название сайта")
    prompt: str = Field(description="Промпт, по которому создан сайт")

    created_at: datetime = Field(
        serialization_alias="createdAt",
        description="Дата и время создания",
    )
    updated_at: datetime = Field(
        serialization_alias="updatedAt",
        description="Дата и время последнего обновления",
    )

    view_html_url: str = Field(
        serialization_alias="htmlCodeUrl",
        description="Ссылка на просмотр HTML",
    )
    download_html_url: str = Field(
        serialization_alias="htmlCodeDownloadUrl",
        description="Ссылка на скачивание HTML",
    )
    screenshot_url: str = Field(
        serialization_alias="screenshotUrl",
        description="Ссылка на скриншот сайта",
    )

    urlPath: str = Field(
        default="",
        description="Путь сайта для frontend",
    )


class SitesListResponse(BaseModel):
    sites: list[SiteDetailResponse] = Field(description="Список сайтов текущего пользователя")


class GenerateRequest(BaseModel):
    prompt: str = Field(description="Промпт для перегенерации")
