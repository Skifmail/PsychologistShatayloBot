from aiogram import Dispatcher, types, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, date
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Appointment, Client
from database.session import SessionLocal
from sqlalchemy import select
from states.psychologist_states import DateQueryState
from config import PSYCHOLOGIST_ID
from keyboards.reply import schedule_main_keyboard

# 📋 Кнопки выбора периода
async def choose_records_filter(message: Message):
    if message.from_user.id != PSYCHOLOGIST_ID:
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗓 На сегодня", callback_data="records_today")],
            [InlineKeyboardButton(text="📅 На завтра", callback_data="records_tomorrow")],
            [InlineKeyboardButton(text="📆 На неделю", callback_data="records_week")],
            [InlineKeyboardButton(text="📅 Выбрать дату", callback_data="records_date")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="records_back")]
        ]
    )
    await message.answer("📋 Выберите период для отображения записей:", reply_markup=kb)

# 🔙 Обработка "Назад"
async def records_back(callback: CallbackQuery):
    if callback.from_user.id != PSYCHOLOGIST_ID:
        return

    await callback.message.delete()
    await callback.message.answer("↩️ Вы вернулись в меню психолога.", reply_markup=schedule_main_keyboard())

# 🗓 Обработка "На сегодня"
async def show_today(callback: CallbackQuery):
    if callback.from_user.id != PSYCHOLOGIST_ID:
        return

    await callback.message.delete()
    await show_grouped_appointments(callback.message, datetime.now().date())

# 🗓 Обработка "На завтра"
async def show_records_tomorrow(callback: CallbackQuery):
    if callback.from_user.id != PSYCHOLOGIST_ID:
        return

    await callback.message.delete()

    tomorrow = datetime.now().date() + timedelta(days=1)
    now = datetime.now()

    async with SessionLocal() as session:
        query = await session.execute(
            select(Appointment).where(
                Appointment.date_time >= datetime.combine(tomorrow, datetime.min.time()),
                Appointment.date_time <= datetime.combine(tomorrow, datetime.max.time())
            ).order_by(Appointment.date_time)
        )
        appointments = query.scalars().all()

        filtered = [
            a for a in appointments
            if a.status in ["active", "confirmed"] and a.date_time >= now
        ]

        if not filtered:
            await callback.message.answer("📭 На завтра нет активных записей.")
            return

        for a in filtered:
            client = await session.get(Client, a.client_id)
            name = client.full_name if client else "Неизвестный"
            phone = getattr(client, "phone_number", "—")
            time = a.date_time.strftime('%H:%M')
            date_str = tomorrow.strftime('%d.%m.%Y')

            text = f"📅 <b>{date_str}</b>\n• {time} — {name} ({phone}) — {a.service}"
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(
                    text=f"❌ Отменить {time}",
                    callback_data=f"cancel_{a.id}"
                )]]
            )
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


# 📆 Обработка "На неделю"
async def show_week_grouped(callback: CallbackQuery):
    if callback.from_user.id != PSYCHOLOGIST_ID:
        return

    await callback.message.delete()

    today = datetime.now().date()
    now = datetime.now()

    async with SessionLocal() as session:
        has_records = False

        for i in range(7):
            date = today + timedelta(days=i)
            query = await session.execute(
                select(Appointment).where(
                    Appointment.date_time >= datetime.combine(date, datetime.min.time()),
                    Appointment.date_time <= datetime.combine(date, datetime.max.time())
                ).order_by(Appointment.date_time)
            )
            appointments = query.scalars().all()

            for a in appointments:
                if a.status not in ["confirmed", "active"]:
                    continue
                if a.date_time < now:
                    continue

                client = await session.get(Client, a.client_id)
                name = client.full_name if client else "Неизвестный"
                phone = getattr(client, "phone_number", "—")
                time = a.date_time.strftime('%H:%M')
                date_str = date.strftime('%d.%m.%Y')

                text = f"📅 <b>{date_str}</b>\n• {time} — {name} ({phone}) — {a.service}"
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(
                        text=f"❌ Отменить {time}",
                        callback_data=f"cancel_{a.id}"
                    )]]
                )
                await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
                has_records = True

        if not has_records:
            await callback.message.answer("📭 На этой неделе нет активных записей.")


# 📅 FSM: старт запроса даты
async def start_date_query(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != PSYCHOLOGIST_ID:
        return

    await callback.message.edit_text("📅 Введите дату (ДД.ММ.ГГГГ):")
    await state.set_state(DateQueryState.date)

# 📅 FSM: получить дату
async def receive_date(message: Message, state: FSMContext):
    if message.from_user.id != PSYCHOLOGIST_ID:
        return

    try:
        selected = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
        await state.clear()
        await show_grouped_appointments(message, selected)
    except ValueError:
        await message.answer("❌ Неверный формат. Попробуйте ДД.ММ.ГГГГ.")

# 📋 Вывод записей по дате
async def show_grouped_appointments(message: Message, date: datetime.date):
    async with SessionLocal() as session:
        query = await session.execute(
            select(Appointment).where(
                Appointment.date_time >= datetime.combine(date, datetime.min.time()),
                Appointment.date_time <= datetime.combine(date, datetime.max.time())
            ).order_by(Appointment.date_time)
        )
        appointments = query.scalars().all()

        now = datetime.now()
        found = False  # 🔹 Отслеживаем, есть ли записи

        for a in appointments:
            if a.status not in ["confirmed", "active"]:
                continue  # ❌ Пропускаем отменённые и нерелевантные

            if a.date_time < now:
                continue  # ❌ Пропускаем прошедшие

            client = await session.get(Client, a.client_id)
            name = client.full_name if client else "Неизвестный"
            phone = getattr(client, "phone_number", "—")
            time = a.date_time.strftime('%H:%M')

            line = f"• {time} — {name} ({phone}) — {a.service}"
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"❌ Отменить {time}", callback_data=f"cancel_{a.id}")]
                ]
            )
            await message.answer(line, reply_markup=kb)
            found = True

        if not found:
            await message.answer(f"📭 Нет актуальных записей на {date.strftime('%d.%m.%Y')}")


# 🔗 Регистрация хэндлеров
def register_records_handlers(dp: Dispatcher):
    dp.message.register(choose_records_filter, F.text == "📋 Показать записи")
    dp.callback_query.register(show_today, F.data == "records_today")
    dp.callback_query.register(show_records_tomorrow, F.data == "records_tomorrow")
    dp.callback_query.register(show_week_grouped, F.data == "records_week")
    dp.callback_query.register(start_date_query, F.data == "records_date")
    dp.callback_query.register(records_back, F.data == "records_back")
    dp.message.register(receive_date, DateQueryState.date)
