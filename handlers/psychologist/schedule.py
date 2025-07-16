"""
Хэндлеры для просмотра и редактирования расписания психолога, ручное закрытие слотов.
"""
import logging
from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import datetime
from sqlalchemy import select
from database.session import get_session
from database.models import WorkSchedule, UnavailableSlot
from states.psychologist_states import ScheduleStates
from keyboards.reply import schedule_main_keyboard
from utils.decorators import psychologist_only

@psychologist_only
async def view_schedule(message: types.Message) -> None:
    """Показать текущее расписание психолога."""
    async for session in get_session():
        query = await session.execute(select(WorkSchedule))
        slots = query.scalars().all()
        if not slots:
            await message.answer("📭 Расписание пусто. Рабочих часов не найдено.")
            return
        text = "🗓 Текущее расписание:\n\n"
        for slot in slots:
            weekday = slot.weekday
            start = slot.start_time.strftime("%H:%M")
            end = slot.end_time.strftime("%H:%M")
            text += f"• День: {weekday} — {start} до {end}\n"
        await message.answer(text)

@psychologist_only
async def choose_date(message: types.Message, state: FSMContext) -> None:
    """Старт FSM для ручного закрытия слота: запрос даты."""
    await message.answer("📅 Введите дату, когда вы будете недоступны (ГГГГ-ММ-ДД):")
    await state.set_state(ScheduleStates.date)

@psychologist_only
async def get_date(message: types.Message, state: FSMContext) -> None:
    """Получить дату для ручного закрытия слота."""
    try:
        date_ = datetime.strptime(message.text.strip(), "%Y-%m-%d").date()
        await state.update_data(date=date_)
        await message.answer("⏰ Укажите время начала недоступности (ЧЧ:ММ):")
        await state.set_state(ScheduleStates.start_time)
    except Exception as e:
        logging.error(f"Ошибка парсинга даты: {e}")
        await message.answer("❌ Некорректный формат даты.")

@psychologist_only
async def get_start_time(message: types.Message, state: FSMContext) -> None:
    """Получить время начала недоступности."""
    try:
        start = datetime.strptime(message.text.strip(), "%H:%M").time()
        await state.update_data(start=start)
        await message.answer("⏳ Укажите время окончания недоступности (ЧЧ:ММ):")
        await state.set_state(ScheduleStates.end_time)
    except Exception as e:
        logging.error(f"Ошибка парсинга времени: {e}")
        await message.answer("❌ Некорректное время. Используйте формат ЧЧ:ММ.")

@psychologist_only
async def get_end_time(message: types.Message, state: FSMContext) -> None:
    """Получить время окончания недоступности и сохранить слот."""
    try:
        end = datetime.strptime(message.text.strip(), "%H:%M").time()
        data = await state.get_data()
        start_dt = datetime.combine(data["date"], data["start"])
        end_dt = datetime.combine(data["date"], end)
        async for session in get_session():
            slot = UnavailableSlot(
                date_time_start=start_dt,
                date_time_end=end_dt,
                reason="Ручное закрытие"
            )
            session.add(slot)
            await session.commit()
        await message.answer("✅ Слот закрыт для записи.")
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка в формате времени: {e}")
        await message.answer("❌ Ошибка в формате времени.")

def register_schedule_handlers(dp: Dispatcher) -> None:
    """Регистрация хэндлеров для работы с расписанием психолога."""
    dp.message.register(view_schedule, Command("schedule"))
    dp.message.register(choose_date, F.text == "🗓 Указать недоступное время")
    dp.message.register(get_date, ScheduleStates.date)
    dp.message.register(get_start_time, ScheduleStates.start_time)
    dp.message.register(get_end_time, ScheduleStates.end_time)




# from aiogram import Dispatcher, types, F
# from aiogram.fsm.context import FSMContext
# from aiogram.filters import Command
# from datetime import datetime
# from sqlalchemy import select
# from database.session import SessionLocal
# from database.models import WorkSchedule, UnavailableSlot
# from states.psychologist_states import ScheduleStates
# from keyboards.reply import schedule_main_keyboard
# from utils.decorators import psychologist_only
#
#
# # 📅 Хэндлер просмотра расписания
# @psychologist_only
# async def view_schedule(message: types.Message):
#     async with SessionLocal() as session:
#         query = await session.execute(select(WorkSchedule))
#         slots = query.scalars().all()
#
#         if not slots:
#             await message.answer("📭 Расписание пусто. Рабочих часов не найдено.")
#             return
#
#         text = "🗓 Текущее расписание:\n\n"
#         for slot in slots:
#             weekday = slot.weekday
#             start = slot.start_time.strftime("%H:%M")
#             end = slot.end_time.strftime("%H:%M")
#             text += f"• День: {weekday} — {start} до {end}\n"
#
#         await message.answer(text)
#
#
# # 🗓 FSM — ручное закрытие недоступного времени
# @psychologist_only
# async def choose_date(message: types.Message, state: FSMContext):
#     await message.answer("📅 Введите дату, когда вы будете недоступны (ГГГГ-ММ-ДД):")
#     await state.set_state(ScheduleStates.date)
# @psychologist_only
# async def get_date(message: types.Message, state: FSMContext):
#     try:
#         date = datetime.strptime(message.text.strip(), "%Y-%m-%d").date()
#         await state.update_data(date=date)
#         await message.answer("⏰ Укажите время начала недоступности (ЧЧ:ММ):")
#         await state.set_state(ScheduleStates.start_time)
#     except ValueError:
#         await message.answer("❌ Некорректный формат даты.")
# @psychologist_only
# async def get_start_time(message: types.Message, state: FSMContext):
#     try:
#         start = datetime.strptime(message.text.strip(), "%H:%M").time()
#         await state.update_data(start=start)
#         await message.answer("⏳ Укажите время окончания недоступности (ЧЧ:ММ):")
#         await state.set_state(ScheduleStates.end_time)
#     except ValueError:
#         await message.answer("❌ Некорректное время. Используйте формат ЧЧ:ММ.")
# @psychologist_only
# async def get_end_time(message: types.Message, state: FSMContext):
#     try:
#         end = datetime.strptime(message.text.strip(), "%H:%M").time()
#         data = await state.get_data()
#
#         start_dt = datetime.combine(data["date"], data["start"])
#         end_dt = datetime.combine(data["date"], end)
#
#         async with SessionLocal() as session:
#             slot = UnavailableSlot(
#                 date_time_start=start_dt,
#                 date_time_end=end_dt,
#                 reason="Ручное закрытие"
#             )
#             session.add(slot)
#             await session.commit()
#
#         await message.answer("✅ Слот закрыт для записи.")
#         await state.clear()
#     except ValueError:
#         await message.answer("❌ Ошибка в формате времени.")
#
#
# # 🔗 Регистрация всех хэндлеров расписания
# def register_schedule_handlers(dp: Dispatcher):
#     dp.message.register(view_schedule, Command("schedule"))
#     dp.message.register(choose_date, F.text == "🗓 Указать недоступное время")
#     dp.message.register(get_date, ScheduleStates.date)
#     dp.message.register(get_start_time, ScheduleStates.start_time)
#     dp.message.register(get_end_time, ScheduleStates.end_time)
