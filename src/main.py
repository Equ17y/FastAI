import asyncio
import json
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Path as FastAPIPath, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient
from pydantic import BaseModel, Field

from env_settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение работы клиентов при старте/остановке приложения."""

    print("\n=== Инициализация клиентов API ===")

    ds_key = settings.deepseek.api_key.get_secret_value()
    ds_base_url = settings.deepseek.base_url
    ds_model = settings.deepseek.model
    ds_timeout = settings.deepseek.timeout

    us_key = settings.unsplash.api_key.get_secret_value()
    us_timeout = settings.unsplash.timeout

    async with AsyncExitStack() as stack:
        app.state.unsplash_client = await stack.enter_async_context(
            AsyncUnsplashClient.setup(us_key, timeout=us_timeout),
        )
        app.state.deepseek_client = await stack.enter_async_context(
            AsyncDeepseekClient.setup(ds_key, ds_base_url, ds_model, timeout=ds_timeout),
        )

        print("✅ Клиенты DeepSeek и Unsplash успешно инициализированы!")
        print("===========================\n")

        # Выводим настройки
        print("=== APP SETTINGS (JSON) ===")
        print(json.dumps(settings.model_dump(mode="json"), indent=2, ensure_ascii=False))
        print("===========================\n")

        yield

    print("\n=== Завершение работы клиентов API ===")


app = FastAPI(lifespan=lifespan)

SiteTitle = Annotated[str, Field(min_length=1, max_length=100, description="Название сайта")]


class UserResponse(BaseModel):
    id: int = Field(description="Уникальный идентификатор пользователя")
    email: str = Field(description="Электронная почта пользователя")
    username: str = Field(description="Имя пользователя (логин)")
    registrated_at: str = Field(description="Дата и время регистрации")
    is_active: bool = Field(description="Статус активности аккаунта")


class SiteCreateRequest(BaseModel):
    title: SiteTitle = Field(default="Мой новый сайт", description="Название сайта")
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
    htmlCodeUrl: str = Field(description="URL HTML-кода для iframe")


class SitesListResponse(BaseModel):
    sites: list[SiteDetailResponse] = Field(description="Список сайтов текущего пользователя")


class GenerateRequest(BaseModel):
    prompt: str = Field(description="Промпт для перегенерации")


def get_mock_site(site_id: int, title: str = "Мой тестовый сайт", prompt: str = "Сделай красиво") -> dict:
    view_url = f"http://127.0.0.1:8000/sites/{site_id}/view"
    download_url = f"http://127.0.0.1:8000/sites/{site_id}/download"
    return {
        "id": site_id,
        "title": title,
        "prompt": prompt,
        "created_at": "2023-10-25T10:00:00Z",
        "updated_at": "2023-10-25T10:00:00Z",
        "view_html_url": view_url,
        "download_html_url": download_url,
        "screenshot_url": "https://placehold.co/100x100/png",
        "htmlCodeUrl": view_url,
    }


@app.get("/users/me", response_model=UserResponse, tags=["Users"])
async def get_current_user():
    return {
        "id": 1,
        "email": "ivan.petrov@example.com",
        "username": "ivan_petrov",
        "registrated_at": "2023-10-25T10:00:00Z",
        "is_active": True,
    }


@app.post("/sites/create", response_model=SiteDetailResponse, tags=["Sites"])
async def create_site(request: SiteCreateRequest):
    return get_mock_site(site_id=1, title=request.title, prompt=request.prompt)


@app.get(
    "/sites/my",
    response_model=SitesListResponse,
    tags=["Sites"],
)
async def get_my_sites():
    return {
        "sites": [
            get_mock_site(
                site_id=1,
                title="Сайт про котиков",
                prompt="Сайт с котиками",
            ),
            get_mock_site(
                site_id=2,
                title="Мой блог",
                prompt="Личный блог",
            ),
        ],
    }


@app.get("/sites/{site_id}", response_model=SiteDetailResponse, tags=["Sites"])
async def get_site(
    site_id: int = FastAPIPath(description="ID сайта", ge=1),
):
    return get_mock_site(site_id=site_id)


@app.get("/sites/{site_id}/view", tags=["Sites"])
async def view_site(site_id: int = FastAPIPath(description="ID сайта", ge=1)):
    return FileResponse("index.html")


@app.get("/sites/{site_id}/download", tags=["Sites"])
async def download_site(site_id: int = FastAPIPath(description="ID сайта", ge=1)):
    return FileResponse(
        "index.html",
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=index.html"},
    )


async def stream_html_generation(prompt: str, request: Request):
    """Отдельная функция для снижения сложности (C901) и генерации HTML."""
    async with (
        AsyncUnsplashClient.setup(
            settings.unsplash.api_key.get_secret_value(),
            timeout=settings.unsplash.timeout,
        ),
        AsyncDeepseekClient.setup(
            settings.deepseek.api_key.get_secret_value(),
            settings.deepseek.base_url,
            settings.deepseek.model,
            timeout=settings.deepseek.timeout,
        ),
    ):
        generator = AsyncPageGenerator(debug_mode=False)

        async for chunk in generator(prompt):
            # STORY-510: Проверка отключения клиента
            if await request.is_disconnected():
                print("\n⚠️ Клиент отключился. Генерация остановлена.")
                break

            if isinstance(chunk, bytes):
                yield chunk
            elif isinstance(chunk, str):
                yield chunk.encode()  # ruff уже убрал отсюда "utf-8"
            else:
                yield str(chunk).encode()

        # Сохранение файла
        output_file = Path("index.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(generator.html_page.html_code)

        yield f"\n\n<!-- Сайт успешно сгенерирован и сохранен в {output_file} -->".encode()


@app.post("/sites/{site_id}/generate", tags=["Sites"])
async def generate_site_streaming(
    request: Request,
    site_id: int = FastAPIPath(description="ID сайта", ge=1),
    req_body: GenerateRequest = None,
):
    prompt = req_body.prompt if req_body and req_body.prompt else "Современный одностраничный сайт"

    async def html_stream():
        try:
            async for chunk in stream_html_generation(prompt, request):
                yield chunk
        except asyncio.CancelledError:
            print("\n⚠️ Генерация отменена (CancelScope сработал корректно).")
        except Exception as e:
            import traceback

            error_msg = f"\n\nОшибка генерации: {type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
            yield error_msg.encode()

    return StreamingResponse(html_stream(), media_type="text/html")


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@app.get("/")
async def read_root():
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
