"""
Хэндлеры для записи клиента к психологу (FSM: имя, телефон, услуга, дата, время, подтверждение).
"""
import logging
from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from states.client_states import BookingStates
from keyboards.inline import service_keyboard, confirm_keyboard
from keyboards.reply import client_main_keyboard, schedule_main_keyboard
from config import PSYCHOLOGIST_ID
from database.session import get_session
from database.models import Appointment, Client
from sqlalchemy import select, and_
from datetime import datetime
from services.slots import get_available_slots, get_available_days
from aiogram.exceptions import TelegramBadRequest

BLOCKED_INPUTS = ["📅 Записаться", "🗓 Мои записи", "📋 О боте", "🔙 Назад"]

async def start_handler(message: types.Message, state: FSMContext) -> None:
    """Запуск FSM для клиента: проверка роли, запрос ФИО или переход к выбору услуги."""
    user_id = message.from_user.id
    if user_id == PSYCHOLOGIST_ID:
        await message.answer("🚫 Вы — психолог. Записываться к себе нельзя 🙂", reply_markup=schedule_main_keyboard())
        return
    async for session in get_session():
        client_q = await session.execute(select(Client).where(Client.telegram_id == user_id))
        client = client_q.scalar()
        if client:
            await state.update_data(full_name=client.full_name, phone=client.phone_number)
            await message.answer("🛎 Выберите услугу:", reply_markup=service_keyboard())
            await state.set_state(BookingStates.service)
        else:
            await message.answer(
                "👋 Добро пожаловать! Чтобы записаться, укажите ваше <b>ФИО</b>:",
                parse_mode="HTML"
            )
            await state.set_state(BookingStates.full_name)

def register_client_handlers(dp: Dispatcher) -> None:
    """Регистрация хэндлеров FSM для записи клиента."""
    dp.message.register(start_handler, Command("start"))

    @dp.message(BookingStates.full_name)
    async def get_full_name(message: types.Message, state: FSMContext) -> None:
        if message.text in BLOCKED_INPUTS:
            await message.answer("❌ Введите ваше имя вручную, без использования кнопок.")
            return
        await state.update_data(full_name=message.text)
        await message.answer("📞 Укажите ваш номер телефона:")
        await state.set_state(BookingStates.phone)

    @dp.message(BookingStates.phone)
    async def get_phone(message: types.Message, state: FSMContext) -> None:
        if message.text in BLOCKED_INPUTS:
            await message.answer("❌ Введите номер телефона вручную.")
            return
        await state.update_data(phone=message.text)
        await message.answer("🛎 Выберите услугу:", reply_markup=service_keyboard())
        await state.set_state(BookingStates.service)

    @dp.callback_query(BookingStates.service, F.data.startswith("service_"))
    async def select_service(callback: types.CallbackQuery, state: FSMContext) -> None:
        service = callback.data.replace("service_", "")
        await state.update_data(service=service)
        available_dates = await get_available_days(10)
        if not available_dates:
            try:
                await callback.message.edit_text("🗓 Нет доступных дней для записи.")
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
            return
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=label, callback_data=f"date_{date.strftime('%Y-%m-%d')}")]
                for label, date in available_dates
            ]
        )
        try:
            await callback.message.edit_text("📅 Выберите день:", reply_markup=kb)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await state.set_state(BookingStates.date)

    @dp.callback_query(BookingStates.date, F.data.startswith("date_"))
    async def select_date(callback: types.CallbackQuery, state: FSMContext) -> None:
        date_str = callback.data.replace("date_", "")
        try:
            chosen_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception as e:
            logging.error(f"Ошибка парсинга даты: {e}")
            await callback.message.answer("Ошибка даты. Попробуйте снова.")
            return
        await state.update_data(date=chosen_date)
        slots = await get_available_slots(chosen_date)
        if not slots:
            try:
                await callback.message.edit_text("⚠️ На эту дату слоты закончились.")
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
            return
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=time, callback_data=f"time_{time}")]
                for time in slots
            ]
        )
        try:
            await callback.message.edit_text("⏰ Выберите время:", reply_markup=kb)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await state.set_state(BookingStates.time)

    @dp.callback_query(BookingStates.time, F.data.startswith("time_"))
    async def select_time(callback: types.CallbackQuery, state: FSMContext) -> None:
        time_str = callback.data.replace("time_", "")
        try:
            chosen_time = datetime.strptime(time_str, "%H:%M").time()
        except Exception as e:
            logging.error(f"Ошибка парсинга времени: {e}")
            await callback.message.answer("Ошибка времени. Попробуйте снова.")
            return
        await state.update_data(time=chosen_time)
        data = await state.get_data()
        if "date" not in data:
            await callback.message.answer("Ошибка: не выбрана дата.")
            return
        dt_str = datetime.combine(data["date"], chosen_time).strftime('%d.%m.%Y %H:%M')
        try:
            await callback.message.edit_text(
                f"Вы хотите записаться на <b>{dt_str}</b>?",
                reply_markup=confirm_keyboard(),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await state.set_state(BookingStates.confirm)

    @dp.callback_query(BookingStates.confirm, F.data == "confirm_yes")
    async def confirm_booking(callback: types.CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        try:
            appointment_dt = datetime.combine(data["date"], data["time"])
        except Exception as e:
            logging.error(f"Ошибка при формировании даты и времени: {e}")
            await callback.message.answer("Ошибка даты/времени. Попробуйте снова.")
            return
        async for session in get_session():
            client_q = await session.execute(
                select(Client).where(
                    and_(
                        Client.full_name == data["full_name"],
                        Client.phone_number == data["phone"]
                    )
                )
            )
            client = client_q.scalar()
            if not client:
                client = Client(
                    full_name=data["full_name"],
                    phone_number=data["phone"],
                    telegram_id=callback.from_user.id
                )
                session.add(client)
                await session.commit()
                await session.refresh(client)
            elif client.telegram_id is None:
                client.telegram_id = callback.from_user.id
                await session.commit()
            appointment = Appointment(
                client_id=client.id,
                date_time=appointment_dt,
                service=data["service"],
                status="active",
                confirmed=None
            )
            session.add(appointment)
            await session.commit()
        try:
            await callback.message.edit_text("✅ Запись сохранена! Мы напомним вам за 24 часа.")
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await state.clear()

    @dp.callback_query(BookingStates.confirm, F.data == "confirm_no")
    async def cancel_booking(callback: types.CallbackQuery, state: FSMContext) -> None:
        try:
            await callback.message.edit_text("❌ Вы отменили запись. Если передумаете — начните снова.")
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await state.clear()