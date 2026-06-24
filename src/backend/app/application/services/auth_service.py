import uuid

from passlib.hash import argon2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dtos import TokenResponse, UserResponse
from app.infrastructure.auth import create_access_token, decode_access_token
from app.infrastructure.persistence.models.user import UserModel


class AuthService:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def register(self, username: str, email: str, password: str, display_name: str) -> TokenResponse | None:
        stmt = select(UserModel).where(
            (UserModel.username == username) | (UserModel.email == email)
        )
        result = await self._session.execute(stmt)
        if result.scalars().first():
            return None

        user = UserModel(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password_hash=argon2.hash(password),
            display_name=display_name or username,
            is_active=True,
        )
        self._session.add(user)
        await self._session.flush()

        token = create_access_token(str(user.id), user.username)
        return TokenResponse(
            accessToken=token,
            userId=str(user.id),
            username=user.username,
            displayName=user.display_name,
        )

    async def login(self, username: str, password: str) -> TokenResponse | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        user = result.scalars().first()
        if not user or not user.is_active:
            return None

        if not argon2.verify(password, user.password_hash):
            return None

        token = create_access_token(str(user.id), user.username)
        return TokenResponse(
            accessToken=token,
            userId=str(user.id),
            username=user.username,
            displayName=user.display_name,
        )

    async def get_current_user(self, token: str) -> UserResponse | None:
        payload = decode_access_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        stmt = select(UserModel).where(UserModel.id == uuid.UUID(user_id))
        result = await self._session.execute(stmt)
        user = result.scalars().first()
        if not user or not user.is_active:
            return None

        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            displayName=user.display_name,
            isActive=user.is_active,
        )
