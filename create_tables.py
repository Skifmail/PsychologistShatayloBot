"""
Утилита для создания таблиц в базе данных.

Запускает асинхронное создание всех таблиц на основе моделей SQLAlchemy.
Используется для инициализации базы данных перед первым запуском приложения.
"""
import asyncio
import logging

from database.models import Base
from database.session import engine


async def create() -> None:
    """
    Создать все таблицы в базе данных.
    
    Выполняет синхронный вызов Base.metadata.create_all() через
    асинхронное соединение для создания всех таблиц, определённых
    в моделях SQLAlchemy.
    
    Raises:
        Exception: При ошибке подключения к БД или создания таблиц
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Таблицы успешно созданы в базе данных")
    except Exception as e:
        logging.exception(f"Ошибка при создании таблиц: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(create())
