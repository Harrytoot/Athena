from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.feature_store.models import FeatureModel


@dataclass
class FeatureItem:
    name: str
    value: float
    category: str
    timestamp: datetime
    version: str
    source: str
    confidence: float


class FeatureRepository(ABC):

    @abstractmethod
    async def save(self, feature: FeatureItem) -> None:
        ...

    @abstractmethod
    async def save_batch(self, features: list[FeatureItem]) -> None:
        ...

    @abstractmethod
    async def get_latest(self, name: str) -> Optional[FeatureItem]:
        ...

    @abstractmethod
    async def get_history(
        self, name: str, since: datetime, until: datetime
    ) -> list[FeatureItem]:
        ...


class InMemoryFeatureRepository(FeatureRepository):

    def __init__(self):
        self._store: list[FeatureItem] = []

    async def save(self, feature: FeatureItem) -> None:
        self._store.append(feature)

    async def save_batch(self, features: list[FeatureItem]) -> None:
        self._store.extend(features)

    async def get_latest(self, name: str) -> Optional[FeatureItem]:
        matches = [f for f in self._store if f.name == name]
        return max(matches, key=lambda f: f.timestamp) if matches else None

    async def get_history(
        self, name: str, since: datetime, until: datetime
    ) -> list[FeatureItem]:
        return [
            f
            for f in self._store
            if f.name == name and since <= f.timestamp <= until
        ]


class SQLAlchemyFeatureRepository(FeatureRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, feature: FeatureItem) -> None:
        model = FeatureModel(
            name=feature.name,
            value=feature.value,
            category=feature.category,
            timestamp=feature.timestamp,
            version=feature.version,
            source=feature.source,
            confidence=feature.confidence,
        )
        self._session.add(model)

    async def save_batch(self, features: list[FeatureItem]) -> None:
        for feature in features:
            await self.save(feature)

    async def get_latest(self, name: str) -> Optional[FeatureItem]:
        stmt = (
            select(FeatureModel)
            .where(FeatureModel.name == name)
            .order_by(FeatureModel.timestamp.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_item(model) if model else None

    async def get_history(
        self, name: str, since: datetime, until: datetime
    ) -> list[FeatureItem]:
        stmt = (
            select(FeatureModel)
            .where(
                FeatureModel.name == name,
                FeatureModel.timestamp >= since,
                FeatureModel.timestamp <= until,
            )
            .order_by(FeatureModel.timestamp.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_item(row) for row in result.scalars().all()]

    @staticmethod
    def _to_item(model: FeatureModel) -> FeatureItem:
        return FeatureItem(
            name=model.name,
            value=model.value,
            category=model.category,
            timestamp=model.timestamp,
            version=model.version,
            source=model.source,
            confidence=model.confidence,
        )
