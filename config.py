import os
from dotenv import load_dotenv

# 📦 Загружаем переменные из .env
load_dotenv()

# 🔐 Токен Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не задан в .env")

# 🗄 Конфигурация базы данных
DB_CONFIG = {
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "psychologist_bot_db"),
}

DB_URL = (
    f"postgresql+asyncpg://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)
PSYCHOLOGIST_ID = int(os.getenv("PSYCHOLOGIST_ID"))
