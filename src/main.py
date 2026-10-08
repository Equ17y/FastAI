import asyncio
import json
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Annotated

import aioboto3
import httpx
from botocore.config import Config
from fastapi import FastAPI, Path as FastAPIPath, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from gotenberg_api import ScreenshotHTMLRequest
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

    s3_config = Config(
        connect_timeout=settings.aws.connect_timeout,
        read_timeout=settings.aws.read_timeout,
        max_pool_connections=settings.aws.max_connections,
    )

    async with AsyncExitStack() as stack:
        app.state.generation_tasks = set()

        app.state.unsplash_client = await stack.enter_async_context(
            AsyncUnsplashClient.setup(us_key, timeout=us_timeout),
        )
        app.state.deepseek_client = await stack.enter_async_context(
            AsyncDeepseekClient.setup(ds_key, ds_base_url, ds_model, timeout=ds_timeout),
        )

        s3_session = aioboto3.Session()

        app.state.s3_client = await stack.enter_async_context(
            s3_session.client(
                "s3",
                endpoint_url=settings.aws.endpoint_url,
                aws_access_key_id=settings.aws.access_key.get_secret_value(),
                aws_secret_access_key=settings.aws.secret_key.get_secret_value(),
                config=s3_config,
            ),
        )

        app.state.gotenberg_client = await stack.enter_async_context(
            httpx.AsyncClient(
                base_url=settings.gotenberg.api_url,
                timeout=httpx.Timeout(settings.gotenberg.timeout),
                limits=httpx.Limits(
                    max_connections=settings.gotenberg.max_connections,
                    max_keepalive_connections=settings.gotenberg.max_connections,
                ),
            ),
        )

        print("Клиенты DeepSeek, Unsplash, S3 и Gotenberg успешно инициализированы!")
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
    htmlCodeUrl: str = Field(description="URL HTML для frontend")
    htmlCodeDownloadUrl: str = Field(description="URL скачивания для frontend")
    screenshotUrl: str = Field(description="URL скриншота для frontend")
    createdAt: str = Field(description="Дата создания для frontend")
    updatedAt: str = Field(description="Дата обновления для frontend")


class SitesListResponse(BaseModel):
    sites: list[SiteDetailResponse] = Field(description="Список сайтов текущего пользователя")


class GenerateRequest(BaseModel):
    prompt: str = Field(description="Промпт для перегенерации")


def get_s3_object_url(object_name: str) -> str:
    endpoint_url = settings.aws.endpoint_url.rstrip("/")
    return f"{endpoint_url}/{settings.aws.bucket_name}/{object_name}"


def get_s3_download_url(object_name: str) -> str:
    object_url = get_s3_object_url(object_name)
    return f"{object_url}?response-content-disposition=attachment"


async def upload_html_to_s3(s3_client, html_code: str) -> None:
    await s3_client.put_object(
        Bucket=settings.aws.bucket_name,
        Key="index.html",
        Body=html_code.encode("utf-8"),
        ContentType="text/html",
        ContentDisposition="inline",
    )


async def upload_screenshot_to_s3(s3_client, screenshot: bytes) -> None:
    await s3_client.put_object(
        Bucket=settings.aws.bucket_name,
        Key="index.png",
        Body=screenshot,
        ContentType="image/png",
        ContentDisposition="inline",
    )


def get_mock_site(
    site_id: int,
    title: str = "Мой тестовый сайт",
    prompt: str = "Сделай красиво",
) -> dict:
    view_url = get_s3_object_url("index.html")
    download_url = get_s3_download_url("index.html")
    screenshot_url = get_s3_object_url("index.png")

    return {
        "id": site_id,
        "title": title,
        "prompt": prompt,
        "created_at": "2023-10-25T10:00:00Z",
        "updated_at": "2023-10-25T10:00:00Z",
        "view_html_url": view_url,
        "download_html_url": download_url,
        "screenshot_url": screenshot_url,
        "urlPath": "",
        "htmlCodeUrl": view_url,
        "htmlCodeDownloadUrl": download_url,
        "screenshotUrl": screenshot_url,
        "createdAt": "2023-10-25T10:00:00Z",
        "updatedAt": "2023-10-25T10:00:00Z",
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


async def generate_html_in_background(
    prompt: str,
    app: FastAPI,
    chunks_queue: asyncio.Queue,
) -> None:
    """Генерирует сайт независимо от HTTP-соединения и сохраняет HTML в S3."""
    generator = AsyncPageGenerator(debug_mode=settings.debug)

    try:
        async for chunk in generator(prompt):
            if isinstance(chunk, bytes):
                chunk_bytes = chunk
            elif isinstance(chunk, str):
                chunk_bytes = chunk.encode()
            else:
                chunk_bytes = str(chunk).encode()

            await chunks_queue.put(chunk_bytes)

        html_code = generator.html_page.html_code

        await upload_html_to_s3(
            app.state.s3_client,
            html_code,
        )
        print("index.html сохранён в S3.")

        screenshot_request = ScreenshotHTMLRequest(
            index_html=html_code,
            width=settings.gotenberg.screenshot_width,
            format=settings.gotenberg.image_format,
            wait_delay=settings.gotenberg.wait_delay,
        )

        screenshot = await screenshot_request.asend(
            app.state.gotenberg_client,
        )

        await upload_screenshot_to_s3(
            app.state.s3_client,
            screenshot,
        )

        print("index.png сохранён в S3.")
        print("\nГенерация сайта и скриншота завершена.")

        await chunks_queue.put(
            b"\n\n<!-- Site successfully generated and saved to S3 -->",
        )

    except Exception as exc:
        import traceback

        error_msg = f"\n\nОшибка генерации: {type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"

        print(error_msg)
        await chunks_queue.put(error_msg.encode())

    finally:
        await chunks_queue.put(None)


@app.post("/sites/{site_id}/generate", tags=["Sites"])
async def generate_site_streaming(
    request: Request,
    site_id: int = FastAPIPath(description="ID сайта", ge=1),
    req_body: GenerateRequest = None,
):
    prompt = req_body.prompt if req_body and req_body.prompt else "Современный одностраничный сайт"

    chunks_queue = asyncio.Queue()

    generation_task = asyncio.create_task(
        generate_html_in_background(
            prompt=prompt,
            app=request.app,
            chunks_queue=chunks_queue,
        ),
    )

    request.app.state.generation_tasks.add(generation_task)
    generation_task.add_done_callback(
        request.app.state.generation_tasks.discard,
    )

    async def html_stream():
        while True:
            chunk = await chunks_queue.get()

            if chunk is None:
                break

            yield chunk

    return StreamingResponse(
        html_stream(),
        media_type="text/html",
    )


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@app.get("/")
async def read_root():
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
