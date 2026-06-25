from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.models.user import UserModel


class UserRepositoryImpl(UserRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def create(self, user: User) -> User:
        model = UserModel(
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        user.id = str(model.id)
        return user

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=str(model.id),
            username=model.username,
            email=model.email,
            display_name=model.display_name or "",
            password_hash=model.password_hash or "",
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
