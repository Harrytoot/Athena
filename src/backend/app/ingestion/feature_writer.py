import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.feature_store.models import FeatureModel
from app.feature_store.repository import FeatureItem
from app.infrastructure.cache.redis import get_redis

logger = logging.getLogger(__name__)

REDIS_FEATURE_KEY = "athena:feature:latest"


class FeatureWriter:
    async def write_features(
        self, features: list[FeatureItem], session: AsyncSession
    ) -> None:
        for item in features:
            model = FeatureModel(
                name=item.name,
                value=item.value,
                category=item.category,
                timestamp=item.timestamp,
                version=item.version,
                source=item.source,
                confidence=item.confidence,
            )
            session.add(model)

        await session.commit()
        logger.info("Persisted %d features to feature_history", len(features))

        await self._update_cache(features)

    async def _update_cache(self, features: list[FeatureItem]) -> None:
        try:
            redis = await get_redis()
            cache_data: dict[str, str] = {
                item.name: str(round(item.value, 2)) for item in features
            }
            cache_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            cache_data["source"] = features[0].source if features else ""
            await redis.hset(REDIS_FEATURE_KEY, mapping=cache_data)
            await redis.expire(REDIS_FEATURE_KEY, 86400)
            logger.info("Updated Redis cache at %s", REDIS_FEATURE_KEY)
        except Exception as e:
            logger.warning("Failed to update Redis cache: %s", e)
