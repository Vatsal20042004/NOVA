"""
Database session configuration
Async SQLAlchemy setup with PostgreSQL
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Create async engine - SQLite doesn't support pooling options
if settings.is_sqlite:
    engine = create_async_engine(
        settings.async_database_url,
        echo=settings.DATABASE_ECHO,
        connect_args={"check_same_thread": False},
    )
    engine_nullpool = engine  # Same engine for SQLite
else:
    engine = create_async_engine(
        settings.async_database_url,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,  # Enable connection health checks
    )
    # For testing or serverless, use NullPool
    engine_nullpool = create_async_engine(
        settings.async_database_url,
        echo=settings.DATABASE_ECHO,
        poolclass=NullPool,
    )

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # CRITICAL for async - prevents DetachedInstanceError
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_transactional() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions with explicit transaction control.
    Use this when you need manual transaction management.
    """
    async with async_session_maker() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
