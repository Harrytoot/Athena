from abc import ABC, abstractmethod

from app.domain.entities.user import User


class UserRepository(ABC):

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def create(self, user: User) -> User:
        ...
