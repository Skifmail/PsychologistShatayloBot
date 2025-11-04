"""
Главный модуль запуска Telegram-бота психолога.

Этот модуль является точкой входа в приложение. Он инициализирует бота,
регистрирует все обработчики команд и запускает планировщик для автоматических
уведомлений клиентам.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from services.scheduler import schedule_reminders, send_missed_day_reminders
from handlers.client.menu import register_user_menu
from handlers.client.booking import register_client_handlers
from handlers.client.cancel import register_cancel_handlers
from handlers.client.reminders import register_reminder_handlers
from handlers.client.reschedule import register_reschedule_handlers
from handlers.psychologist.menu import register_psychologist_menu
from handlers.psychologist.schedule import register_schedule_handlers
from handlers.psychologist.work_hours import register_work_hours_handlers
from handlers.psychologist.records import register_records_handlers


async def main() -> None:
    """
    Главная асинхронная функция для запуска бота.
    
    Выполняет следующие действия:
    1. Настраивает логирование
    2. Инициализирует бота с HTML-парсингом по умолчанию
    3. Создаёт диспетчер с хранилищем состояний в памяти
    4. Регистрирует все обработчики для клиентов и психолога
    5. Запускает планировщик напоминаний
    6. Отправляет пропущенные напоминания (если бот был выключен)
    7. Начинает polling для получения обновлений от Telegram
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.info("Запуск Telegram-бота психолога...")
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация обработчиков для клиентов
    register_client_handlers(dp)
    register_cancel_handlers(dp)
    register_reminder_handlers(dp)
    register_reschedule_handlers(dp)
    register_user_menu(dp)

    # Регистрация обработчиков для психолога
    register_psychologist_menu(dp)
    register_schedule_handlers(dp)
    register_work_hours_handlers(dp)
    register_records_handlers(dp)

    # Запуск планировщика напоминаний
    schedule_reminders(bot)
    await send_missed_day_reminders(bot)
    
    logging.info("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.exception(f"Критическая ошибка при запуске бота: {e}")
