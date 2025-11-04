"""
Модуль для управления соединениями с базой данных.

Предоставляет асинхронный движок SQLAlchemy и фабрику сессий для работы
с базой данных PostgreSQL.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from config import DB_URL


engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный генератор сессий базы данных.
    
    Создаёт и предоставляет асинхронную сессию SQLAlchemy для выполнения
    запросов к базе данных. Автоматически закрывает сессию после использования.
    
    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy
        
    Example:
        ```python
        async for session in get_session():
            result = await session.execute(select(Client))
            clients = result.scalars().all()
        ```
    """
    async with SessionLocal() as session:
        yield session
