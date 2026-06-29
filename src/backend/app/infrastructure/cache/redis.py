import logging
from typing import Any

from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

redis_client: Any = None


class InMemoryRedis:
    """In-memory Redis-compatible cache for development without Redis server."""

    def __init__(self):
        self._hash: dict[str, dict] = {}
        self._set_store: dict[str, set] = {}
        self._lists: dict[str, list] = {}

    async def hset(self, name, key=None, value=None, mapping=None):
        if name not in self._hash:
            self._hash[name] = {}
        if mapping:
            self._hash[name].update({k: str(v) for k, v in mapping.items()})
            return len(mapping)
        if key is not None:
            self._hash[name][key] = str(value)
            return 1
        return 0

    async def hgetall(self, name):
        return self._hash.get(name, {})

    async def hget(self, name, key):
        return self._hash.get(name, {}).get(key)

    async def delete(self, *names):
        count = 0
        for name in names:
            if name in self._hash:
                del self._hash[name]
                count += 1
            if name in self._set_store:
                del self._set_store[name]
                count += 1
            if name in self._lists:
                del self._lists[name]
                count += 1
        return count

    async def rpush(self, name, *values):
        if name not in self._lists:
            self._lists[name] = []
        self._lists[name].extend([str(v) for v in values])
        return len(self._lists[name])

    async def lrange(self, name, start, end):
        lst = self._lists.get(name, [])
        if end == -1:
            return lst[start:]
        return lst[start:end + 1]

    async def expire(self, name, time):
        return True

    async def set(self, name, value, ex=None):
        self._hash[name] = {"__value__": str(value)}
        return True

    async def get(self, name):
        return self._hash.get(name, {}).get("__value__")

    async def sadd(self, name, *values):
        if name not in self._set_store:
            self._set_store[name] = set()
        self._set_store[name].update([str(v) for v in values])
        return len(values)

    async def smembers(self, name):
        return list(self._set_store.get(name, set()))

    async def exists(self, *names):
        count = 0
        for name in names:
            if name in self._hash or name in self._set_store or name in self._lists:
                count += 1
        return count

    async def ping(self):
        return True

    async def close(self):
        self._hash.clear()
        self._set_store.clear()
        self._lists.clear()


async def get_redis() -> Any:
    global redis_client
    if redis_client is None:
        if not settings.REDIS_ENABLED:
            logger.info("Redis disabled, using in-memory cache")
            redis_client = InMemoryRedis()
        else:
            try:
                redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
                await redis_client.ping()
                logger.info("Connected to Redis at %s", settings.REDIS_URL)
            except Exception:
                logger.warning("Redis unavailable at %s, using in-memory cache", settings.REDIS_URL)
                redis_client = InMemoryRedis()
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
        except Exception:
            pass
        redis_client = None
