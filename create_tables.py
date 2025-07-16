"""
Модуль для создания всех таблиц в базе данных.
"""
import asyncio
import logging

from database.models import Base
from database.session import engine

async def create() -> None:
    """Создаёт все таблицы в базе данных."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Таблицы успешно созданы.")
    except Exception as e:
        logging.exception(f"Ошибка при создании таблиц: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(create())




# # create_tables.py
#
# from database.models import Base
# from database.session import engine
# import asyncio
#
# async def create():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
# asyncio.run(create())
