from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from datetime import datetime
from database.session import SessionLocal
from database.models import Appointment
from states.client_states import BookingStates
from services.slots import get_available_days, get_available_slots

# 📅 Выбор новой даты
async def reschedule_start(callback: types.CallbackQuery, state: FSMContext):
    appointment_id = int(callback.data.replace("reschedule_", ""))
    await state.set_state(BookingStates.reschedule)
    await state.update_data(old_appointment_id=appointment_id)

    available_dates = await get_available_days(10)
    if not available_dates:
        await callback.message.edit_text("🗓 Нет доступных дат для переноса.")
        return

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=label, callback_data=f"resched_date_{date.strftime('%Y-%m-%d')}")]
            for label, date in available_dates
        ]
    )

    await callback.message.edit_text("📅 Выберите новую дату:", reply_markup=kb)

# ⏰ Выбор нового времени
async def reschedule_date(callback: types.CallbackQuery, state: FSMContext):
    date_str = callback.data.replace("resched_date_", "")
    new_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    await state.update_data(new_date=new_date)

    slots = await get_available_slots(new_date)
    if not slots:
        await callback.message.edit_text("⚠️ Нет доступного времени на эту дату.")
        return

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=time, callback_data=f"resched_time_{time}")]
            for time in slots
        ]
    )
    await callback.message.edit_text("⏰ Выберите новое время:", reply_markup=kb)

# ✅ Сохранение нового времени
async def reschedule_time(callback: types.CallbackQuery, state: FSMContext):
    time_str = callback.data.replace("resched_time_", "")
    new_time = datetime.strptime(time_str, "%H:%M").time()
    data = await state.get_data()

    new_dt = datetime.combine(data["new_date"], new_time)

    async with SessionLocal() as session:
        query = await session.execute(
            select(Appointment).where(Appointment.id == data["old_appointment_id"])
        )
        appointment = query.scalar()

        if appointment and appointment.status == "active":
            appointment.date_time = new_dt
            appointment.confirmed = None
            await session.commit()
            await callback.message.edit_text(
                f"✅ Запись перенесена на {new_dt.strftime('%d.%m.%Y %H:%M')}."
            )
        else:
            await callback.message.edit_text("⚠️ Запись недействительна для переноса.")

    await state.clear()

def register_reschedule_handlers(dp: Dispatcher):
    dp.callback_query.register(reschedule_start, F.data.startswith("reschedule_"))
    dp.callback_query.register(reschedule_date, F.data.startswith("resched_date_"), BookingStates.reschedule)
    dp.callback_query.register(reschedule_time, F.data.startswith("resched_time_"), BookingStates.reschedule)
