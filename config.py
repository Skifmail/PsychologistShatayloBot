"""
Модуль конфигурации проекта.

Загружает переменные окружения из файла .env и предоставляет настройки для:
- Подключения к Telegram Bot API
- Подключения к базе данных PostgreSQL
- Идентификации психолога в системе

Raises:
    ValueError: Если обязательные переменные окружения (BOT_TOKEN, PSYCHOLOGIST_ID)
                не заданы в файле .env
"""
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env файле")


def get_db_config() -> Dict[str, str]:
    """
    Получить конфигурацию подключения к базе данных из переменных окружения.
    
    Returns:
        Dict[str, str]: Словарь с параметрами подключения к PostgreSQL:
            - user: имя пользователя БД (по умолчанию 'postgres')
            - password: пароль пользователя БД (по умолчанию 'postgres')
            - host: хост сервера БД (по умолчанию 'localhost')
            - port: порт сервера БД (по умолчанию '5432')
            - database: имя базы данных (по умолчанию 'psychologist_bot_db')
    """
    return {
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "psychologist_bot_db"),
    }


DB_CONFIG = get_db_config()

DB_URL = (
    f"postgresql+asyncpg://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

_psych_id = os.getenv("PSYCHOLOGIST_ID")
if _psych_id is None:
    raise ValueError("PSYCHOLOGIST_ID не задан в .env файле")

PSYCHOLOGIST_ID: int = int(_psych_id)
