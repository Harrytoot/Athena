from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_auth_service, get_current_user
from app.application.dtos.auth_dtos import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.application.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    result = await service.register(
        username=data.username,
        email=data.email,
        password=data.password,
        display_name=data.display_name,
    )
    if not result:
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")
    return result


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, service: AuthService = Depends(get_auth_service)):
    result = await service.login(data.username, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserResponse = Depends(get_current_user)):
    return user
