"""
Модуль для создания асинхронного движка и фабрики сессий SQLAlchemy.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DB_URL
from typing import AsyncGenerator

# 🔌 Создание движка и фабрики сессий
engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор для получения сессии (использовать через async with)."""
    async with SessionLocal() as session:
        yield session
