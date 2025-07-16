"""
Хэндлеры переноса записи клиентом (выбор новой даты и времени, сохранение).
"""
import logging
from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from datetime import datetime
from database.session import get_session
from database.models import Appointment
from states.client_states import BookingStates
from services.slots import get_available_days, get_available_slots
from aiogram.exceptions import TelegramBadRequest

async def reschedule_start(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Старт переноса: выбор новой даты."""
    appointment_id = callback.data.replace("reschedule_", "") if callback.data else None
    if not appointment_id or not appointment_id.isdigit():
        await callback.message.answer("Ошибка: некорректный ID записи.")
        return
    appointment_id = int(appointment_id)
    await state.set_state(BookingStates.reschedule)
    await state.update_data(old_appointment_id=appointment_id)
    available_dates = await get_available_days(10)
    if not available_dates:
        try:
            await callback.message.edit_text("🗓 Нет доступных дат для переноса.")
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        return
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=label, callback_data=f"resched_date_{date.strftime('%Y-%m-%d')}")]
            for label, date in available_dates
        ]
    )
    try:
        await callback.message.edit_text("📅 Выберите новую дату:", reply_markup=kb)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

async def reschedule_date(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Выбор нового времени после даты."""
    date_str = callback.data.replace("resched_date_", "") if callback.data else None
    if not date_str:
        await callback.message.answer("Ошибка: некорректная дата.")
        return
    try:
        new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception as e:
        logging.error(f"Ошибка парсинга даты: {e}")
        await callback.message.answer("Ошибка даты. Попробуйте снова.")
        return
    await state.update_data(new_date=new_date)
    slots = await get_available_slots(new_date)
    if not slots:
        try:
            await callback.message.edit_text("⚠️ Нет доступного времени на эту дату.")
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        return
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=time, callback_data=f"resched_time_{time}")]
            for time in slots
        ]
    )
    try:
        await callback.message.edit_text("⏰ Выберите новое время:", reply_markup=kb)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

async def reschedule_time(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Сохранение нового времени переноса."""
    time_str = callback.data.replace("resched_time_", "") if callback.data else None
    if not time_str:
        await callback.message.answer("Ошибка: некорректное время.")
        return
    try:
        new_time = datetime.strptime(time_str, "%H:%M").time()
    except Exception as e:
        logging.error(f"Ошибка парсинга времени: {e}")
        await callback.message.answer("Ошибка времени. Попробуйте снова.")
        return
    data = await state.get_data()
    if "new_date" not in data or "old_appointment_id" not in data:
        await callback.message.answer("Ошибка: не выбрана дата или запись.")
        return
    new_dt = datetime.combine(data["new_date"], new_time)
    async for session in get_session():
        query = await session.execute(
            select(Appointment).where(Appointment.id == data["old_appointment_id"])
        )
        appointment = query.scalar()
        if appointment and getattr(appointment, 'status', None) == "active":
            setattr(appointment, 'date_time', new_dt)
            setattr(appointment, 'confirmed', None)
            await session.commit()
            try:
                await callback.message.edit_text(
                    f"✅ Запись перенесена на {new_dt.strftime('%d.%m.%Y %H:%M')}."
                )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
        else:
            try:
                await callback.message.edit_text("⚠️ Запись недействительна для переноса.")
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
    await state.clear()

def register_reschedule_handlers(dp: Dispatcher) -> None:
    """Регистрация хэндлеров переноса записи."""
    dp.callback_query.register(reschedule_start, F.data.startswith("reschedule_"))
    dp.callback_query.register(reschedule_date, F.data.startswith("resched_date_"), BookingStates.reschedule)
    dp.callback_query.register(reschedule_time, F.data.startswith("resched_time_"), BookingStates.reschedule)
