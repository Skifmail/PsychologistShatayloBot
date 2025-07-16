"""
Главный модуль запуска Telegram-бота психолога.
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
    """Точка входа для запуска бота."""
    logging.basicConfig(level=logging.INFO)
    logging.info("Запуск Telegram-бота психолога...")
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 🚀 Регистрация хэндлеров
    register_client_handlers(dp)
    register_cancel_handlers(dp)
    register_reminder_handlers(dp)
    register_reschedule_handlers(dp)
    register_user_menu(dp)

    register_psychologist_menu(dp)
    register_schedule_handlers(dp)
    register_work_hours_handlers(dp)
    register_records_handlers(dp)

    # ⏰ Планировщик
    schedule_reminders(bot)
    await send_missed_day_reminders(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.exception(f"Ошибка при запуске бота: {e}")




# import asyncio
# from aiogram import Bot, Dispatcher
# from aiogram.enums import ParseMode
# from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.client.default import DefaultBotProperties
# from config import BOT_TOKEN
# from services.scheduler import schedule_reminders, send_missed_day_reminders
# from handlers.client.menu import register_user_menu
# from handlers.client.booking import register_client_handlers
# from handlers.client.cancel import register_cancel_handlers
# from handlers.client.reminders import register_reminder_handlers
# from handlers.client.reschedule import register_reschedule_handlers
#
# from handlers.psychologist.menu import register_psychologist_menu
# from handlers.psychologist.schedule import register_schedule_handlers
# from handlers.psychologist.work_hours import register_work_hours_handlers
# from handlers.psychologist.records import register_records_handlers
#
# async def main():
#     bot = Bot(
#         token=BOT_TOKEN,
#         default=DefaultBotProperties(parse_mode=ParseMode.HTML)
#     )
#     dp = Dispatcher(storage=MemoryStorage())
#
#     # 🚀 Регистрация хэндлеров
#     register_client_handlers(dp)
#     register_cancel_handlers(dp)
#     register_reminder_handlers(dp)
#     register_reschedule_handlers(dp)
#     register_user_menu(dp)
#
#     register_psychologist_menu(dp)
#     register_schedule_handlers(dp)
#     register_work_hours_handlers(dp)
#     register_records_handlers(dp)
#
#     # ⏰ Планировщик
#     schedule_reminders(bot)
#     await send_missed_day_reminders(bot)
#     await dp.start_polling(bot)
#
# if __name__ == "__main__":
#     asyncio.run(main())
