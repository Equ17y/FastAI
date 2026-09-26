import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Path as FastAPIPath
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
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
    htmlCodeUrl: str = Field(description="URL HTML-кода для iframe (camelCase для фронтенда)")


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
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Сгенерированный сайт #{site_id}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 40px; background: #f5f5f5;
                }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
            h1 {{ color: #333; }}
            p {{ color: #666; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Сгенерированный сайт #{site_id}</h1>
            <p>Это мок-ответ для демонстрации работы генератора сайтов FastAI.</p>
            <p>Здесь должен отображаться HTML-код, сгенерированный нейросетью.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/sites/{site_id}/download", tags=["Sites"])
async def download_site(site_id: int = FastAPIPath(description="ID сайта", ge=1)):
    html_content = f"""<!DOCTYPE html>
<html><head><title>Site {site_id}</title></head>
<body><h1>Generated Site #{site_id}</h1><p>Mock HTML for download.</p></body>
</html>"""
    return HTMLResponse(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=site_{site_id}.html"},
    )


@app.post("/sites/{site_id}/generate", tags=["Sites"])
async def generate_site_streaming(
    site_id: int = FastAPIPath(description="ID сайта", ge=1),
    request: GenerateRequest = None,
):
    async def html_stream():
        chunks = [
            b"<html><head><title>Generating...</title></head><body>",
            b"<h1>Starting site generation...</h1>",
            b"<p>Loading resources...</p>",
            b"<p>Applying styles...</p>",
            b"<h2 style='color: green;'>Site generated successfully!</h2>",
            b"<p>Mock response for StreamingResponse test.</p>",
            b"</body></html>",
        ]
        for chunk in chunks:
            yield chunk
            await asyncio.sleep(0.5)

    return StreamingResponse(html_stream(), media_type="text/html")


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@app.get("/")
async def read_root():
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
