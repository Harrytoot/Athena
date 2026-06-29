from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

_db_url = settings.DATABASE_URL

if _db_url.startswith("sqlite"):
    engine = create_async_engine(_db_url, echo=False, poolclass=NullPool)
else:
    engine = create_async_engine(_db_url, echo=False, pool_size=5, max_overflow=10)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
