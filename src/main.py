import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Path as FastAPIPath
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI()

SiteTitle = Annotated[str, Field(min_length=1, max_length=100, description="Название сайта")]


class UserResponse(BaseModel):
    id: int = Field(description="Уникальный идентификатор пользователя")
    email: str = Field(description="Электронная почта пользователя")
    username: str = Field(description="Имя пользователя (логин)")
    registrated_at: str = Field(description="Дата и время регистрации")
    is_active: bool = Field(description="Статус активности аккаунта")


class SiteCreateRequest(BaseModel):
    title: SiteTitle
    prompt: str = Field(description="Промпт для генерации сайта")


class SiteDetailResponse(BaseModel):
    id: int = Field(description="ID сайта")
    title: str = Field(description="Название сайта")
    prompt: str = Field(description="Промпт, по которому создан сайт")
    created_at: str = Field(description="Дата и время создания")
    updated_at: str = Field(description="Дата и время последнего обновления")
    view_html_url: str = Field(description="Ссылка на просмотр сайта")
    download_html_url: str = Field(description="Ссылка на скачивание HTML")
    screenshot_url: str = Field(description="Ссылка на скриншот сайта")


class GenerateRequest(BaseModel):
    prompt: str = Field(description="Промпт для перегенерации")


def get_mock_site(site_id: int, title: str = "Мой тестовый сайт", prompt: str = "Сделай красиво") -> dict:
    """Возвращает одинаковые правдоподобные данные для любого site_id"""
    return {
        "id": site_id,
        "title": title,
        "prompt": prompt,
        "created_at": "2023-10-25T10:00:00Z",
        "updated_at": "2023-10-25T10:00:00Z",
        # Используем реальный URL, чтобы фронтенд мог его открыть (как в задании)
        "view_html_url": "https://google.com",
        "download_html_url": "https://google.com",
        "screenshot_url": "https://google.com/favicon.ico",
    }


@app.get("/users/me", response_model=UserResponse)
async def get_current_user():
    """
    Возвращает моковые (фиктивные) данные профиля пользователя.
    """
    return {
        "id": 1,
        "email": "ivan.petrov@example.com",
        "username": "ivan_petrov",
        "registrated_at": "2023-10-25T10:00:00Z",
        "is_active": True,
    }


@app.post("/sites/create", response_model=SiteDetailResponse, tags=["Sites"])
async def create_site(request: SiteCreateRequest):
    """STORY-505: Создание сайта."""
    # Возвращаем мок с ID = 1 для простоты
    return get_mock_site(site_id=1, title=request.title, prompt=request.prompt)


@app.get("/sites/my", response_model=list[SiteDetailResponse], tags=["Sites"])
async def get_my_sites():
    """STORY-334: Получение списка сайтов пользователя."""
    # Возвращаем список из 2-х моковых сайтов
    return [
        get_mock_site(site_id=1, title="Сайт про котиков", prompt="Сайт с котиками"),
        get_mock_site(site_id=2, title="Мой блог", prompt="Личный блог"),
    ]


@app.get("/sites/{site_id}", response_model=SiteDetailResponse, tags=["Sites"])
async def get_site(
    site_id: int = FastAPIPath(description="ID сайта", ge=1),
):
    """STORY-328: Получение данных конкретного сайта."""
    return get_mock_site(site_id=site_id)


@app.post("/sites/{site_id}/generate", tags=["Sites"])
async def generate_site_streaming(
    site_id: int = FastAPIPath(description="ID сайта", ge=1),
    request: GenerateRequest = None,
):
    """
    STORY-156: Получение HTML-кода сайта стримингом.
    Имитирует долгую генерацию, отдавая HTML частями.
    """

    async def html_stream():
        # ВАЖНО: В байтовых строках (b"...") используем только ASCII (латиницу)!
        chunks = [
            b"<html><head><title>Generating...</title></head><body>",
            b"<h1>Starting site generation...</h1>",
            b"<p>Loading resources...</p>",
            b"<p>Applying styles...</p>",
            b"<h2 style='color: green;'>Site generated successfully!</h2>",
            b"<p>This is a mock response for testing StreamingResponse.</p>",
            b"</body></html>",
        ]
        for chunk in chunks:
            yield chunk
            await asyncio.sleep(0.5)  # Имитация задержки генерации

    return StreamingResponse(html_stream(), media_type="text/html")


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@app.get("/")
async def read_root():
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
