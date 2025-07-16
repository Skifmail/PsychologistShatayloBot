"""
Хэндлеры отмены записи клиентом или психологом, FSM для причины отмены.
"""
import logging
from aiogram import Dispatcher, types, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database.session import get_session
from database.models import Appointment, Client
from sqlalchemy import select, and_
from datetime import datetime
from config import PSYCHOLOGIST_ID

class CancelState(StatesGroup):
    """FSM-состояния для причины отмены записи."""
    reason = State()

# Хранилище id записи (по пользователю)
cancel_context = {}

SERVICE_LABELS = {
    "consult": "Консультация",
    "intro": "Первая встреча",
    "supervision": "Супервизия"
}

async def my_appointments(message: Message):
    """Показать клиенту его активные записи с кнопками отмены/переноса."""
    if message is None or getattr(message, 'answer', None) is None:
        return
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        await message.answer("Ошибка: не удалось определить пользователя.")
        return
    async for session in get_session():
        client_q = await session.execute(select(Client).where(Client.telegram_id == user_id))
        client = client_q.scalar()
        if not client:
            await message.answer("❌ Вы ещё не записывались. Я вас не узнаю 🤷‍♂️")
            return
        now = datetime.now()
        query = await session.execute(
            select(Appointment).where(
                and_(
                    Appointment.client_id == client.id,
                    Appointment.date_time >= now,
                    Appointment.status == "active"
                )
            ).order_by(Appointment.date_time)
        )
        appointments = query.scalars().all()
        if not appointments:
            await message.answer("📭 У вас нет активных записей.")
            return
        text = "📋 Ваши записи:\n\n"
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        for a in appointments:
            dt = a.date_time.strftime("%d.%m.%Y %H:%M")
            service_code = str(a.service)
            service_label = SERVICE_LABELS.get(service_code, service_code)
            text += f"• {dt} — {service_label}\n"
            kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"❌ Отменить {dt}", callback_data=f"cancel_{a.id}"),
                InlineKeyboardButton(text=f"🔁 Перенести {dt}", callback_data=f"reschedule_{a.id}")
            ])
        await message.answer(text.strip(), reply_markup=kb)

async def start_cancel(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия на отмену записи: психологу — запрос причины, клиенту — отмена сразу."""
    if callback is None or getattr(callback.message, 'answer', None) is None:
        return
    user_id = getattr(callback.from_user, 'id', None)
    if user_id is None:
        await callback.message.answer("Ошибка: не удалось определить пользователя.")
        return
    appointment_id = callback.data.replace("cancel_", "") if callback.data else None
    if not appointment_id or not appointment_id.isdigit():
        await callback.message.answer("Ошибка: некорректный ID записи.")
        return
    appointment_id = int(appointment_id)
    cancel_context[user_id] = appointment_id
    if user_id == PSYCHOLOGIST_ID:
        await callback.message.answer("💬 Введите причину отмены для клиента:")
        await state.set_state(CancelState.reason)
    else:
        async for session in get_session():
            appointment = await session.get(Appointment, appointment_id)
            if appointment and getattr(appointment, 'status', None) == "active":
                setattr(appointment, 'status', "cancelled")
                setattr(appointment, 'confirmed', False)
                await session.commit()
        if getattr(callback.message, 'edit_text', None):
            await callback.message.edit_text("❌ Запись успешно отменена.")

async def receive_cancel_reason(message: Message, state: FSMContext, bot: Bot):
    """Психолог вводит причину отмены — клиенту отправляется уведомление."""
    if message is None or getattr(message, 'answer', None) is None:
        return
    text = getattr(message, 'text', None)
    reason = text.strip() if text else ""
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        await message.answer("Ошибка: не удалось определить пользователя.")
        await state.clear()
        return
    appointment_id = cancel_context.get(user_id)
    if not appointment_id:
        await message.answer("❌ Не удалось найти запись.")
        await state.clear()
        return
    async for session in get_session():
        appointment = await session.get(Appointment, appointment_id)
        client = await session.get(Client, appointment.client_id) if appointment else None
        if not appointment or not client:
            await message.answer("❌ Ошибка при получении данных.")
            await state.clear()
            return
        setattr(appointment, 'status', "cancelled")
        setattr(appointment, 'confirmed', False)
        await session.commit()
        client_telegram_id = getattr(client, 'telegram_id', None)
        if client_telegram_id is not None and isinstance(client_telegram_id, int):
            try:
                await bot.send_message(
                    chat_id=client_telegram_id,
                    text=(
                        f"❌ Ваша запись <b>{appointment.service}</b> на {appointment.date_time.strftime('%d.%m.%Y %H:%M')} отменена.\n\n"
                        f"💬 Причина: {reason}"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке уведомления клиенту: {e}")
        await message.answer("✅ Запись отменена. Клиент уведомлён.")
        cancel_context.pop(user_id, None)
        await state.clear()

def register_cancel_handlers(dp: Dispatcher):
    """Регистрация хэндлеров отмены записи."""
    dp.message.register(my_appointments, Command("my"))
    dp.callback_query.register(start_cancel, F.data.startswith("cancel_"))
    dp.message.register(receive_cancel_reason, CancelState.reason)




# from aiogram import Dispatcher, types, F, Bot
# from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
# from aiogram.filters import Command
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import StatesGroup, State
# from database.session import SessionLocal
# from database.models import Appointment, Client
# from sqlalchemy import select, and_
# from datetime import datetime
# from config import PSYCHOLOGIST_ID
#
# # 🧠 FSM: причина отмены
# class CancelState(StatesGroup):
#     reason = State()
#
# # Хранилище id записи (по пользователю)
# cancel_context = {}
#
# # 📋 Хэндлер для просмотра записей клиента
# async def my_appointments(message: Message):
#     user_id = message.from_user.id
#
#     async with SessionLocal() as session:
#         client_q = await session.execute(select(Client).where(Client.telegram_id == user_id))
#         client = client_q.scalar()
#
#         if not client:
#             await message.answer("❌ Вы ещё не записывались. Я вас не узнаю 🤷‍♂️")
#             return
#
#         now = datetime.now()
#         query = await session.execute(
#             select(Appointment).where(
#                 and_(
#                     Appointment.client_id == client.id,
#                     Appointment.date_time >= now,
#                     Appointment.status == "active"
#                 )
#             ).order_by(Appointment.date_time)
#         )
#         appointments = query.scalars().all()
#
#         if not appointments:
#             await message.answer("📭 У вас нет активных записей.")
#             return
#
#         text = "📋 Ваши записи:\n\n"
#         kb = InlineKeyboardMarkup(inline_keyboard=[])
#
#         for a in appointments:
#             dt = a.date_time.strftime("%d.%m.%Y %H:%M")
#             text += f"• {dt} — {a.service}\n"
#             kb.inline_keyboard.append([
#                 InlineKeyboardButton(text=f"❌ Отменить {dt}", callback_data=f"cancel_{a.id}"),
#                 InlineKeyboardButton(text=f"🔁 Перенести {dt}", callback_data=f"reschedule_{a.id}")
#             ])
#
#         await message.answer(text.strip(), reply_markup=kb)
#
# # ❌ Отмена записи психологом — начать
# async def start_cancel(callback: CallbackQuery, state: FSMContext):
#     user_id = callback.from_user.id
#     appointment_id = int(callback.data.replace("cancel_", ""))
#
#     cancel_context[user_id] = appointment_id
#
#     if user_id == PSYCHOLOGIST_ID:
#         await callback.message.answer("💬 Введите причину отмены для клиента:")
#         await state.set_state(CancelState.reason)
#     else:
#         # отмена клиентом
#         async with SessionLocal() as session:
#             appointment = await session.get(Appointment, appointment_id)
#             if appointment and appointment.status == "active":
#                 appointment.status = "cancelled"
#                 appointment.confirmed = False
#                 await session.commit()
#         await callback.message.edit_text("❌ Запись успешно отменена.")
#
# # 💬 Получение причины и отправка клиенту
# async def receive_cancel_reason(message: Message, state: FSMContext, bot: Bot):
#     reason = message.text.strip()
#     user_id = message.from_user.id
#     appointment_id = cancel_context.get(user_id)
#
#     if not appointment_id:
#         await message.answer("❌ Не удалось найти запись.")
#         await state.clear()
#         return
#
#     async with SessionLocal() as session:
#         appointment = await session.get(Appointment, appointment_id)
#         client = await session.get(Client, appointment.client_id) if appointment else None
#
#         if not appointment or not client:
#             await message.answer("❌ Ошибка при получении данных.")
#             await state.clear()
#             return
#
#         appointment.status = "cancelled"
#         appointment.confirmed = False
#         await session.commit()
#
#         if client.telegram_id:
#             await bot.send_message(
#                 chat_id=client.telegram_id,
#                 text=(
#                     f"❌ Ваша запись <b>{appointment.service}</b> на {appointment.date_time.strftime('%d.%m.%Y %H:%M')} отменена.\n\n"
#                     f"💬 Причина: {reason}"
#                 ),
#                 parse_mode="HTML"
#             )
#
#         await message.answer("✅ Запись отменена. Клиент уведомлён.")
#         cancel_context.pop(user_id, None)
#         await state.clear()
#
# # 🔗 Регистрация хэндлеров
# def register_cancel_handlers(dp: Dispatcher):
#     dp.message.register(my_appointments, Command("my"))
#     dp.callback_query.register(start_cancel, F.data.startswith("cancel_"))
#     dp.message.register(receive_cancel_reason, CancelState.reason)
