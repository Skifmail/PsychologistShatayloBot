"""
Хэндлеры клиентского меню: главное меню, информация о боте, возврат назад.
"""
import logging
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from config import PSYCHOLOGIST_ID
from keyboards.reply import client_main_keyboard
from handlers.client.booking import start_handler
from handlers.client.cancel import my_appointments
from aiogram.types import Message
from typing import Awaitable, Any

def show_client_menu(message: types.Message) -> Awaitable[Any]:
    """Показать главное меню клиента."""
    return message.answer("📋 Ваше меню:", reply_markup=client_main_keyboard())

def back_to_client_menu(message: types.Message) -> Awaitable[Any]:
    """Возврат к клиентскому меню."""
    return message.answer("↩️ Вы вернулись в меню клиента.", reply_markup=client_main_keyboard())

def about_bot(message: Message) -> Awaitable[Any]:
    """Информация о боте для клиента."""
    return message.answer(
        "ℹ️ Этот бот позволяет клиентам записываться на консультации, "
        "а психологу — управлять расписанием, приёмами и напоминаниями.\n\n"
        "🧠 Возможности:\n"
        "• Онлайн запись\n"
        "• Управление рабочим временем\n"
        "• Автонаполоминания\n"
        "• Просмотр записей и статистики\n\n"
        "Разработано для психолога 'ФИО' с ❤️"
    )

def register_user_menu(dp: Dispatcher) -> None:
    """Регистрация хэндлеров клиентского меню."""
    dp.message.register(show_client_menu, Command("menu"))
    dp.message.register(about_bot, F.text == "ℹ️ О боте")
    dp.message.register(start_handler, F.text == "📅 Записаться")
    dp.message.register(my_appointments, F.text == "🗓 Мои записи")
