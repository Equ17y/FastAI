from fastapi import APIRouter

from src.schemas.users import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user():
    return {
        "id": 1,
        "email": "ivan.petrov@example.com",
        "username": "ivan_petrov",
        "registrated_at": "2023-10-25T10:00:00Z",
        "is_active": True,
    }
