from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: int = Field(description="Уникальный идентификатор пользователя")
    email: EmailStr = Field(description="Электронная почта пользователя")
    username: str = Field(description="Имя пользователя (логин)")
    registrated_at: datetime = Field(description="Дата и время регистрации")
    is_active: bool = Field(description="Статус активности аккаунта")
