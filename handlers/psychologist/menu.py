"""
Обработчики меню психолога.

Управляет навигацией по меню психолога, обрабатывает переходы к разным разделам
(просмотр записей, настройка расписания, ручная запись клиентов).
"""
import logging
from datetime import datetime

from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from config import PSYCHOLOGIST_ID
from keyboards.reply import schedule_main_keyboard
from states.psychologist_states import ManualBookingStates
from services.slots import get_available_slots
from database.session import get_session
from database.models import Client, Appointment
from handlers.psychologist.records import choose_records_filter
from handlers.psychologist.schedule import view_schedule
from handlers.psychologist.work_hours import edit_work_schedule
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from states.psychologist_states import ManualBookingStates
from services.slots import get_available_slots
from database.session import get_session
from database.models import Client, Appointment
from sqlalchemy import select

async def open_psychologist_menu(message: types.Message) -> None:
    """
    Открыть главное меню психолога.
    
    Проверяет права доступа (только для PSYCHOLOGIST_ID).
    
    Args:
        message: Сообщение с командой /psych
    """
    if not message or not getattr(message, 'from_user', None) or getattr(message.from_user, 'id', 0) == 0:
        logging.error("Пустое сообщение или не определён пользователь.")
        return
    if getattr(message.from_user, 'id', 0) != PSYCHOLOGIST_ID:
        await message.answer("🚫 Доступ запрещён. Это меню только для психолога.")
        return
    await message.answer("📋 Меню психолога:", reply_markup=schedule_main_keyboard())

async def back_to_psychologist_menu(message: types.Message) -> None:
    """Возврат к меню психолога (только для психолога)."""
    if not message or not getattr(message, 'from_user', None) or getattr(message.from_user, 'id', 0) == 0:
        logging.error("Пустое сообщение или не определён пользователь.")
        return
    await message.answer("↩️ Вы вернулись в меню психолога.", reply_markup=schedule_main_keyboard())

async def view_free_slots(message: types.Message, state: FSMContext) -> None:
    """Старт ручной записи: запросить дату."""
    if not message or not getattr(message, 'from_user', None) or getattr(message.from_user, 'id', 0) == 0:
        logging.error("Пустое сообщение или не определён пользователь.")
        return
    if getattr(message.from_user, 'id', 0) != PSYCHOLOGIST_ID:
        await message.answer("🚫 Доступ запрещён. Это меню только для психолога.")
        return
    await message.answer("📅 Введите дату (ДД.ММ.ГГГГ):")
    await state.set_state(ManualBookingStates.date)

async def manual_date(message: types.Message, state: FSMContext) -> None:
    """Получить дату, показать свободные слоты."""
    if not message or not getattr(message, 'text', None):
        await message.answer("❌ Не получен текст сообщения. Попробуйте снова.")
        return
    try:
        date_text = message.text
        if not date_text:
            await message.answer("❌ Не получен текст сообщения. Попробуйте снова.")
            return
        selected = datetime.strptime(date_text.strip(), "%d.%m.%Y").date()
        slots = await get_available_slots(selected)
        if not slots:
            await message.answer("❌ Нет свободных слотов на эту дату. Попробуйте другую дату.")
            return
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=time, callback_data=f"manual_time_{time}")] for time in slots
            ]
        )
        await state.update_data(date=selected)
        await message.answer("⏰ Выберите время:", reply_markup=kb)
        await state.set_state(ManualBookingStates.time)
    except Exception as e:
        logging.error(f"Ошибка парсинга даты: {e}")
        await message.answer("❌ Неверный формат. Попробуйте ДД.ММ.ГГГГ.")

async def manual_time(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Получить время, запросить ФИО клиента."""
    if not callback or not getattr(callback, 'data', None) or not getattr(callback, 'message', None) or not getattr(callback.message, 'answer', None):
        return
    time_data = callback.data
    if not time_data:
        if getattr(callback, 'message', None) and getattr(callback.message, 'answer', None):
            await callback.message.answer("Ошибка: не получены данные слота.")
        return
    time_str = time_data.replace("manual_time_", "")
    try:
        chosen_time = datetime.strptime(time_str, "%H:%M").time()
    except Exception as e:
        logging.error(f"Ошибка парсинга времени: {e}")
        if getattr(callback, 'message', None) and getattr(callback.message, 'answer', None):
            await callback.message.answer("Ошибка времени. Попробуйте снова.")
        return
    await state.update_data(time=chosen_time)
    if getattr(callback, 'message', None) and getattr(callback.message, 'answer', None):
        await callback.message.answer("👤 Введите ФИО клиента:")
    await state.set_state(ManualBookingStates.full_name)

async def manual_full_name(message: types.Message, state: FSMContext) -> None:
    """Получить ФИО, запросить телефон клиента."""
    if not message or not getattr(message, 'text', None):
        await message.answer("❌ Не получено имя клиента. Попробуйте снова.")
        return
    name_text = message.text
    if not name_text:
        await message.answer("❌ Не получено имя клиента. Попробуйте снова.")
        return
    await state.update_data(full_name=name_text.strip())
    await message.answer("📞 Введите телефон клиента:")
    await state.set_state(ManualBookingStates.phone)

async def manual_phone(message: types.Message, state: FSMContext) -> None:
    """Получить телефон, запросить подтверждение."""
    if not message or not getattr(message, 'text', None):
        await message.answer("❌ Не получен телефон клиента. Попробуйте снова.")
        return
    phone_text = message.text
    if not phone_text:
        await message.answer("❌ Не получен телефон клиента. Попробуйте снова.")
        return
    await state.update_data(phone=phone_text.strip())
    data = await state.get_data()
    dt_str = datetime.combine(data["date"], data["time"]).strftime('%d.%m.%Y %H:%M')
    await message.answer(f"Подтвердите запись клиента на <b>{dt_str}</b>\nФИО: {data['full_name']}\nТелефон: {data['phone']}", parse_mode="HTML")
    await message.answer("Напишите 'Да' для подтверждения или 'Нет' для отмены.")
    await state.set_state(ManualBookingStates.confirm)

async def manual_confirm(message: types.Message, state: FSMContext) -> None:
    """Создать запись, если подтверждено. Отправить уведомление клиенту, если есть telegram_id."""
    if not message or not getattr(message, 'text', None):
        await message.answer("❌ Не получен ответ. Попробуйте снова.")
        await state.clear()
        return
    confirm_text = message.text
    if not confirm_text:
        await message.answer("❌ Не получен ответ. Попробуйте снова.")
        await state.clear()
        return
    if confirm_text.strip().lower() != 'да':
        await message.answer("❌ Запись отменена.")
        await state.clear()
        return
    data = await state.get_data()
    appointment_dt = datetime.combine(data["date"], data["time"])
    client = None
    async for session in get_session():
        client_q = await session.execute(
            select(Client).where(
                Client.full_name == data["full_name"],
                Client.phone_number == data["phone"]
            )
        )
        client = client_q.scalar()
        if not client:
            client = Client(
                full_name=data["full_name"],
                phone_number=data["phone"]
            )
            session.add(client)
            await session.commit()
            await session.refresh(client)
        appointment = Appointment(
            client_id=client.id,
            date_time=appointment_dt,
            service="consult",
            status="active",
            confirmed=None
        )
        session.add(appointment)
        await session.commit()
    await message.answer("✅ Запись добавлена! Клиенту будет отправлено напоминание.")
    # Отправить уведомление клиенту, если есть telegram_id
    if client and getattr(client, 'telegram_id', None):
        try:
            notify_text = (
                f"Вы записаны на приём к психологу\n"
                f"Дата: <b>{appointment_dt.strftime('%d.%m.%Y')}</b>\n"
                f"Время: <b>{appointment_dt.strftime('%H:%M')}</b>\n"
                f"Если вы не записывались — проигнорируйте это сообщение."
            )
            telegram_id = int(getattr(client, 'telegram_id'))
            await message.bot.send_message(telegram_id, notify_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления клиенту: {e}")
    await state.clear()

def register_psychologist_menu(dp: Dispatcher) -> None:
    """Регистрация хэндлеров меню психолога."""
    dp.message.register(open_psychologist_menu, Command("psych"))
    dp.message.register(back_to_psychologist_menu, F.text == "🔙 Назад", lambda msg: getattr(getattr(msg, 'from_user', None), 'id', 0) == PSYCHOLOGIST_ID)
    dp.message.register(choose_records_filter, F.text == "📋 Показать записи")
    dp.message.register(view_schedule, F.text == "📆 Расписание")
    dp.message.register(edit_work_schedule, F.text == "🗰 Редактировать рабочее расписание")
    dp.message.register(view_free_slots, F.text == "🔎 Посмотреть свободные слоты")
    dp.message.register(manual_date, ManualBookingStates.date)
    dp.callback_query.register(manual_time, F.data.startswith("manual_time_"), ManualBookingStates.time)
    dp.message.register(manual_full_name, ManualBookingStates.full_name)
    dp.message.register(manual_phone, ManualBookingStates.phone)
    dp.message.register(manual_confirm, ManualBookingStates.confirm)
