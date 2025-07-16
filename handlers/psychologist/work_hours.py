"""
Хэндлеры для просмотра и редактирования рабочих часов психолога.
"""
import logging
from aiogram import Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states.psychologist_states import WorkScheduleStates
from keyboards.reply import weekdays_keyboard, schedule_main_keyboard
from database.session import get_session
from database.models import WorkSchedule
from sqlalchemy import select, update, delete
from datetime import datetime
from utils.decorators import psychologist_only

WEEKDAYS = {
    "Понедельник": 0,
    "Вторник": 1,
    "Среда": 2,
    "Четверг": 3,
    "Пятница": 4,
    "Суббота": 5,
    "Воскресенье": 6
}

def get_day_label(index: int) -> str:
    labels = list(WEEKDAYS.keys())
    return labels[index]

@psychologist_only
async def edit_work_schedule(message: Message, state: FSMContext) -> None:
    """Показать и редактировать рабочее расписание психолога."""
    async for session in get_session():
        query = await session.execute(select(WorkSchedule))
        slots = sorted(query.scalars().all(), key=lambda s: s.weekday)
        msg = "📅 <b>Ваше рабочее расписание:</b>\n"
        if slots:
            msg += "\n".join([
                f"• <b>{get_day_label(s.weekday)}</b>: {s.start_time.strftime('%H:%M')} — {s.end_time.strftime('%H:%M')}"
                for s in slots
            ])
        else:
            msg += "📭 Пока ничего не задано."
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                                [types.InlineKeyboardButton(text="➕ Добавить / Изменить", callback_data="add_schedule")]
                            ] + [
                                [types.InlineKeyboardButton(text=f"🗑 Удалить {get_day_label(s.weekday)}", callback_data=f"delete_{s.weekday}")]
                                for s in slots
                            ]
        )
        await message.answer(msg, parse_mode="HTML", reply_markup=kb)

@psychologist_only
async def start_schedule_fsm(callback: CallbackQuery, state: FSMContext) -> None:
    """Старт FSM для добавления/изменения рабочего дня."""
    await callback.message.answer("📅 Выберите день недели:", reply_markup=weekdays_keyboard())
    await state.set_state(WorkScheduleStates.day)

@psychologist_only
async def get_day(message: Message, state: FSMContext) -> None:
    """Получить день недели для редактирования расписания."""
    day_num = WEEKDAYS.get(message.text)
    if day_num is None:
        await message.answer("❌ Неверный день. Попробуйте снова.")
        return
    await state.update_data(day=day_num, day_label=message.text)
    await message.answer("⏰ Введите время начала работы (например: 10:00):")
    await state.set_state(WorkScheduleStates.start_time)

@psychologist_only
async def get_start_time(message: Message, state: FSMContext) -> None:
    """Получить время начала работы для расписания."""
    try:
        start = datetime.strptime(message.text.strip(), "%H:%M").time()
        await state.update_data(start=start)
        await message.answer("⏳ Введите время окончания работы (например: 18:00):")
        await state.set_state(WorkScheduleStates.end_time)
    except Exception as e:
        logging.error(f"Ошибка парсинга времени: {e}")
        await message.answer("❌ Неверный формат времени. Попробуйте HH:MM.")

@psychologist_only
async def get_end_time(message: Message, state: FSMContext) -> None:
    """Получить время окончания работы и сохранить расписание."""
    try:
        end = datetime.strptime(message.text.strip(), "%H:%M").time()
        data = await state.get_data()
        async for session in get_session():
            query = await session.execute(
                select(WorkSchedule).where(WorkSchedule.weekday == data["day"])
            )
            existing = query.scalar()
            if existing:
                await session.execute(
                    update(WorkSchedule)
                    .where(WorkSchedule.weekday == data["day"])
                    .values(start_time=data["start"], end_time=end)
                )
            else:
                slot = WorkSchedule(
                    weekday=data["day"],
                    start_time=data["start"],
                    end_time=end
                )
                session.add(slot)
            await session.commit()
        await message.answer(
            f"✅ Добавлено: {data['day_label']} — с {data['start'].strftime('%H:%M')} до {end.strftime('%H:%M')}"
        )
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка парсинга времени: {e}")
        await message.answer("❌ Неверный формат времени. Попробуйте HH:MM.")

@psychologist_only
async def cancel_schedule_fsm(message: Message, state: FSMContext) -> None:
    """Отмена FSM редактирования расписания."""
    await state.clear()
    await message.answer("↩️ Вы вернулись в меню психолога.", reply_markup=schedule_main_keyboard())

@psychologist_only
async def delete_schedule(callback: CallbackQuery) -> None:
    """Удалить рабочий день из расписания."""
    day_index = int(callback.data.replace("delete_", "")) if callback.data else None
    if day_index is None:
        await callback.message.answer("Ошибка: некорректный день.")
        return
    async for session in get_session():
        await session.execute(delete(WorkSchedule).where(WorkSchedule.weekday == day_index))
        await session.commit()
    await callback.message.edit_text(f"❌ Расписание для <b>{get_day_label(day_index)}</b> удалено.", parse_mode="HTML")

def register_work_hours_handlers(dp: Dispatcher) -> None:
    """Регистрация хэндлеров для работы с рабочими часами психолога."""
    dp.message.register(edit_work_schedule, F.text == "🗰 Редактировать рабочее расписание")
    dp.callback_query.register(start_schedule_fsm, F.data == "add_schedule")
    dp.message.register(get_day, WorkScheduleStates.day)
    dp.message.register(get_start_time, WorkScheduleStates.start_time)
    dp.message.register(get_end_time, WorkScheduleStates.end_time)
    dp.message.register(cancel_schedule_fsm, F.text == "🔙 Назад")
    dp.callback_query.register(delete_schedule, F.data.startswith("delete_"))





# from aiogram import Dispatcher, types, F
# from aiogram.types import Message, CallbackQuery
# from aiogram.fsm.context import FSMContext
# from states.psychologist_states import WorkScheduleStates
# from keyboards.reply import weekdays_keyboard, schedule_main_keyboard
# from database.session import SessionLocal
# from database.models import WorkSchedule
# from sqlalchemy import select, update, delete
# from datetime import datetime
# from utils.decorators import psychologist_only
#
# WEEKDAYS = {
#     "Понедельник": 0,
#     "Вторник": 1,
#     "Среда": 2,
#     "Четверг": 3,
#     "Пятница": 4,
#     "Суббота": 5,
#     "Воскресенье": 6
# }
#
# def get_day_label(index: int) -> str:
#     labels = list(WEEKDAYS.keys())
#     return labels[index]
#
# # 🛠 Объединённый просмотр и редактирование расписания
# @psychologist_only
# async def edit_work_schedule(message: Message, state: FSMContext):
#     async with SessionLocal() as session:
#         query = await session.execute(select(WorkSchedule))
#         slots = sorted(query.scalars().all(), key=lambda s: s.weekday)
#
#
#         msg = "📅 <b>Ваше рабочее расписание:</b>\n"
#         if slots:
#             msg += "\n".join([
#                 f"• <b>{get_day_label(s.weekday)}</b>: {s.start_time.strftime('%H:%M')} — {s.end_time.strftime('%H:%M')}"
#                 for s in slots
#             ])
#         else:
#             msg += "📭 Пока ничего не задано."
#
#         kb = types.InlineKeyboardMarkup(
#             inline_keyboard=[
#                                 [types.InlineKeyboardButton(text="➕ Добавить / Изменить", callback_data="add_schedule")]
#                             ] + [
#                                 [types.InlineKeyboardButton(text=f"🗑 Удалить {get_day_label(s.weekday)}", callback_data=f"delete_{s.weekday}")]
#                                 for s in slots
#                             ]
#         )
#
#         await message.answer(msg, parse_mode="HTML", reply_markup=kb)
#
# # ⏳ Запуск FSM по кнопке «Добавить / Изменить»
# @psychologist_only
# async def start_schedule_fsm(callback: CallbackQuery, state: FSMContext):
#     await callback.message.answer("📅 Выберите день недели:", reply_markup=weekdays_keyboard())
#     await state.set_state(WorkScheduleStates.day)
#
# # 📅 FSM: Выбор дня
# @psychologist_only
# async def get_day(message: Message, state: FSMContext):
#     day_num = WEEKDAYS.get(message.text)
#     if day_num is None:
#         await message.answer("❌ Неверный день. Попробуйте снова.")
#         return
#
#     await state.update_data(day=day_num, day_label=message.text)
#     await message.answer("⏰ Введите время начала работы (например: 10:00):")
#     await state.set_state(WorkScheduleStates.start_time)
#
# # 🕰 FSM: Время начала
# @psychologist_only
# async def get_start_time(message: Message, state: FSMContext):
#     try:
#         start = datetime.strptime(message.text.strip(), "%H:%M").time()
#         await state.update_data(start=start)
#         await message.answer("⏳ Введите время окончания работы (например: 18:00):")
#         await state.set_state(WorkScheduleStates.end_time)
#     except ValueError:
#         await message.answer("❌ Неверный формат времени. Попробуйте HH:MM.")
#
# # 🕓 FSM: Время окончания — сохранение
# @psychologist_only
# async def get_end_time(message: Message, state: FSMContext):
#     try:
#         end = datetime.strptime(message.text.strip(), "%H:%M").time()
#         data = await state.get_data()
#
#         async with SessionLocal() as session:
#             query = await session.execute(
#                 select(WorkSchedule).where(WorkSchedule.weekday == data["day"])
#             )
#             existing = query.scalar()
#
#             if existing:
#                 await session.execute(
#                     update(WorkSchedule)
#                     .where(WorkSchedule.weekday == data["day"])
#                     .values(start_time=data["start"], end_time=end)
#                 )
#             else:
#                 slot = WorkSchedule(
#                     weekday=data["day"],
#                     start_time=data["start"],
#                     end_time=end
#                 )
#                 session.add(slot)
#
#             await session.commit()
#
#         await message.answer(
#             f"✅ Добавлено: {data['day_label']} — с {data['start'].strftime('%H:%M')} до {end.strftime('%H:%M')}"
#         )
#         await state.clear()
#
#     except ValueError:
#         await message.answer("❌ Неверный формат времени. Попробуйте HH:MM.")
#
# # 🔙 Отмена FSM вручную
# @psychologist_only
# async def cancel_schedule_fsm(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer("↩️ Вы вернулись в меню психолога.", reply_markup=schedule_main_keyboard())
#
# # 🗑 Удаление дня
# @psychologist_only
# async def delete_schedule(callback: CallbackQuery):
#     day_index = int(callback.data.replace("delete_", ""))
#
#     async with SessionLocal() as session:
#         await session.execute(delete(WorkSchedule).where(WorkSchedule.weekday == day_index))
#         await session.commit()
#
#     await callback.message.edit_text(f"❌ Расписание для <b>{get_day_label(day_index)}</b> удалено.", parse_mode="HTML")
#
# # 🔗 Регистрация хэндлеров
# def register_work_hours_handlers(dp: Dispatcher):
#     dp.message.register(edit_work_schedule, F.text == "🕰 Редактировать рабочее расписание")
#     dp.callback_query.register(start_schedule_fsm, F.data == "add_schedule")
#     dp.message.register(get_day, WorkScheduleStates.day)
#     dp.message.register(get_start_time, WorkScheduleStates.start_time)
#     dp.message.register(get_end_time, WorkScheduleStates.end_time)
#     dp.message.register(cancel_schedule_fsm, F.text == "🔙 Назад")
#     dp.callback_query.register(delete_schedule, F.data.startswith("delete_"))
