from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI()


class UserResponse(BaseModel):
    id: int = Field(description="Уникальный идентификатор пользователя")
    email: str = Field(description="Электронная почта пользователя")
    username: str = Field(description="Имя пользователя (логин)")
    registrated_at: str = Field(description="Дата и время регистрации")
    is_active: bool = Field(description="Статус активности аккаунта")


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


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


@app.get("/")
async def read_root():
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
