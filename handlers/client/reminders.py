"""
Хэндлеры подтверждения и отмены записи через inline-кнопки (FSM подтверждения).
"""
import logging
from aiogram import Dispatcher, types, F
from database.session import get_session
from database.models import Appointment, Client
from sqlalchemy import select
from config import PSYCHOLOGIST_ID
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def register_reminder_handlers(dp: Dispatcher) -> None:
    """Регистрация хэндлеров для подтверждения/отмены записи клиентом."""
    @dp.callback_query(F.data.startswith("confirm_"))
    async def handle_confirmation(callback: types.CallbackQuery) -> None:
        try:
            if not callback.data:
                await callback.message.answer("Ошибка: некорректные данные.")
                return
            parts = callback.data.split("_")  # confirm_{appointment_id}_{yes/no}
            if len(parts) < 3 or not parts[1].isdigit():
                await callback.message.answer("Ошибка: некорректные данные.")
                return
            appointment_id = int(parts[1])
            decision = parts[2]
            async for session in get_session():
                appointment = await session.get(Appointment, appointment_id)
                if not appointment or appointment.confirmed is not None:
                    await callback.message.edit_text("✅ Ответ уже получен.")
                    return
                appointment.confirmed = True if decision == "yes" else False
                await session.commit()
                client = await session.get(Client, appointment.client_id)
                if decision == "yes":
                    await callback.message.edit_text("👍 Спасибо, приём подтверждён!")
                else:
                    await callback.message.edit_text("🚫 Запись отменена.")
                psych_text = (
                    f"🧍 Клиент: {getattr(client, 'full_name', '-') if client else '-'}\n"
                    f"📞 Телефон: {getattr(client, 'phone_number', '-') if client else '-'}\n"
                    f"📅 Дата: {appointment.date_time.strftime('%d.%m.%Y %H:%M')}\n"
                    f"📌 Статус: {'подтвердил запись' if decision == 'yes' else 'отменил запись'}"
                )
                await callback.bot.send_message(PSYCHOLOGIST_ID, psych_text)
        except Exception as e:
            logging.error(f"Ошибка при обработке ответа: {e}")
            await callback.message.answer(f"Ошибка при обработке ответа: {str(e)}")





# from aiogram import Dispatcher, types, F
# from database.session import SessionLocal
# from database.models import Appointment, Client
# from sqlalchemy import select
# from config import PSYCHOLOGIST_ID
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
#
# def register_reminder_handlers(dp: Dispatcher):
#
#     @dp.callback_query(F.data.startswith("confirm_"))
#     async def handle_confirmation(callback: types.CallbackQuery):
#         try:
#             parts = callback.data.split("_")  # confirm_{appointment_id}_{yes/no}
#             appointment_id = int(parts[1])
#             decision = parts[2]
#
#             async with SessionLocal() as session:
#                 appointment = await session.get(Appointment, appointment_id)
#                 if not appointment or appointment.confirmed is not None:
#                     await callback.message.edit_text("✅ Ответ уже получен.")
#                     return
#
#                 appointment.confirmed = True if decision == "yes" else False
#                 await session.commit()
#
#                 client = await session.get(Client, appointment.client_id)
#
#                 if decision == "yes":
#                     await callback.message.edit_text("👍 Спасибо, приём подтверждён!")
#                 else:
#                     await callback.message.edit_text("🚫 Запись отменена.")
#
#                 psych_text = (
#                     f"🧍 Клиент: {client.full_name}\n"
#                     f"📞 Телефон: {client.phone_number}\n"
#                     f"📅 Дата: {appointment.date_time.strftime('%d.%m.%Y %H:%M')}\n"
#                     f"📌 Статус: {'подтвердил запись' if decision == 'yes' else 'отменил запись'}"
#                 )
#                 await callback.bot.send_message(PSYCHOLOGIST_ID, psych_text)
#
#         except Exception as e:
#             await callback.message.answer(f"Ошибка при обработке ответа: {str(e)}")
