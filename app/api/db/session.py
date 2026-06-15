from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase , sessionmaker, Session

from app.api.core.config import settings


engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
sync_engine = create_engine(
    settings.POSTGRES_URL.replace("postgresql+asyncpg", "postgresql+psycopg2"),
    pool_size        = 5,
    max_overflow     = 10,
    pool_pre_ping    = True,       
    pool_recycle     = 1800,       
    echo             = False,
)
SyncSessionLocal = sessionmaker(
    bind          = sync_engine,
    autocommit    = False,
    autoflush     = False,
    expire_on_commit = False,
)
def get_sync_session() -> Session:
    """Context manager-safe sync session untuk fetcher."""
    return SyncSessionLocal()
 
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
