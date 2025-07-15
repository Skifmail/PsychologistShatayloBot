from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from config import PSYCHOLOGIST_ID
from keyboards.reply import client_main_keyboard
from handlers.client.booking import start_handler
from handlers.client.cancel import my_appointments
from database.session import SessionLocal
from database.models import Appointment, Client
from sqlalchemy import select
from datetime import datetime
from aiogram.types import Message

# 📋 Команда /menu — клиентское меню
async def show_client_menu(message: types.Message):
    await message.answer("📋 Ваше меню:", reply_markup=client_main_keyboard())

# 🔙 Назад — только для клиента
async def back_to_client_menu(message: types.Message):
    await message.answer("↩️ Вы вернулись в меню клиента.", reply_markup=client_main_keyboard())

# ℹ️ Информация о боте
async def about_bot(message: Message):
    await message.answer(
        "ℹ️ Этот бот позволяет клиентам записываться на консультации, "
        "а психологу — управлять расписанием, приёмами и напоминаниями.\n\n"
        "🧠 Возможности:\n"
        "• Онлайн запись\n"
        "• Управление рабочим временем\n"
        "• Автонапоминания\n"
        "• Просмотр записей и статистики\n\n"
        "Разработано для психолога 'ФИО' с ❤️"
    )

# 🔗 Регистрация хэндлеров клиента
def register_user_menu(dp: Dispatcher):
    dp.message.register(show_client_menu, Command("menu"))
    dp.message.register(about_bot, F.text == "ℹ️ О боте")
    dp.message.register(start_handler, F.text == "📅 Записаться")
    dp.message.register(my_appointments, F.text == "🗓 Мои записи")
