from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import DB_URL

# 🔌 Создание движка и фабрики сессий
engine = create_async_engine(DB_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
