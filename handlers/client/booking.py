"""
Обработчики процесса записи клиента к психологу.

Реализует FSM (конечный автомат) для пошагового процесса записи:
ФИО → Телефон → Услуга → Дата → Время → Подтверждение.

Для существующих клиентов пропускает шаги ФИО и телефона.
"""
import logging
from datetime import datetime

from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, and_

from states.client_states import BookingStates
from keyboards.inline import service_keyboard, confirm_keyboard
from keyboards.reply import client_main_keyboard, schedule_main_keyboard
from config import PSYCHOLOGIST_ID
from database.session import get_session
from database.models import Appointment, Client
from services.slots import get_available_slots, get_available_days

BLOCKED_INPUTS = ["📅 Записаться", "🗓 Мои записи", "📋 О боте", "🔙 Назад"]


async def start_handler(message: types.Message, state: FSMContext) -> None:
    """
    Начать процесс записи клиента.
    
    Проверяет, является ли пользователь психологом (запрещено записываться к себе).
    Для существующих клиентов сразу переходит к выбору услуги.
    Для новых клиентов запрашивает ФИО.
    
    Args:
        message: Сообщение от пользователя с командой /start
        state: Контекст состояния FSM
    """
    user_id = message.from_user.id
    
    # Психологу нельзя записываться к себе
    if user_id == PSYCHOLOGIST_ID:
        await message.answer(
            "🚫 Вы — психолог. Записываться к себе нельзя 🙂",
            reply_markup=schedule_main_keyboard()
        )
        return
    
    # Проверяем, существует ли клиент в базе данных
    async for session in get_session():
        client_q = await session.execute(
            select(Client).where(Client.telegram_id == user_id)
        )
        client = client_q.scalar()
        
        if client:
            # Клиент уже есть — сохраняем его данные и переходим к выбору услуги
            await state.update_data(
                full_name=client.full_name,
                phone=client.phone_number
            )
            await message.answer(
                "🛎 Выберите услугу:",
                reply_markup=service_keyboard()
            )
            await state.set_state(BookingStates.service)
        else:
            # Новый клиент — запрашиваем ФИО
            await message.answer(
                "👋 Добро пожаловать! Чтобы записаться, укажите ваше <b>ФИО</b>:",
                parse_mode="HTML"
            )
            await state.set_state(BookingStates.full_name)


def register_client_handlers(dp: Dispatcher) -> None:
    """
    Зарегистрировать все обработчики процесса записи клиента.
    
    Регистрирует обработчики для каждого шага FSM:
    - Команда /start
    - Ввод ФИО
    - Ввод телефона
    - Выбор услуги (callback)
    - Выбор даты (callback)
    - Выбор времени (callback)
    - Подтверждение записи (callback)
    - Отмена записи (callback)
    
    Args:
        dp: Диспетчер aiogram для регистрации обработчиков
    """
    dp.message.register(start_handler, Command("start"))

    @dp.message(BookingStates.full_name)
    async def get_full_name(message: types.Message, state: FSMContext) -> None:
        """
        Получить ФИО клиента и перейти к запросу телефона.
        
        Блокирует ввод через кнопки меню, требует ручной ввод.
        """
        if message.text in BLOCKED_INPUTS:
            await message.answer(
                "❌ Введите ваше имя вручную, без использования кнопок."
            )
            return
        
        await state.update_data(full_name=message.text)
        await message.answer("📞 Укажите ваш номер телефона:")
        await state.set_state(BookingStates.phone)

    @dp.message(BookingStates.phone)
    async def get_phone(message: types.Message, state: FSMContext) -> None:
        """
        Получить номер телефона клиента и перейти к выбору услуги.
        
        Блокирует ввод через кнопки меню, требует ручной ввод.
        """
        if message.text in BLOCKED_INPUTS:
            await message.answer("❌ Введите номер телефона вручную.")
            return
        
        await state.update_data(phone=message.text)
        await message.answer(
            "🛎 Выберите услугу:",
            reply_markup=service_keyboard()
        )
        await state.set_state(BookingStates.service)

    @dp.callback_query(BookingStates.service, F.data.startswith("service_"))
    async def select_service(callback: types.CallbackQuery, state: FSMContext) -> None:
        """
        Обработать выбор услуги и показать доступные даты.
        
        Загружает список дней с доступными слотами на ближайшие 10 дней.
        Если свободных дней нет, сообщает об этом и завершает процесс.
        """
        service = callback.data.replace("service_", "")
        await state.update_data(service=service)
        
        # Получаем список доступных дней
        available_dates = await get_available_days(10)
        if not available_dates:
            try:
                await callback.message.edit_text(
                    "🗓 Нет доступных дней для записи."
                )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
            return
        
        # Создаём клавиатуру с датами
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=label,
                    callback_data=f"date_{date.strftime('%Y-%m-%d')}"
                )]
                for label, date in available_dates
            ]
        )
        
        try:
            await callback.message.edit_text(
                "📅 Выберите день:",
                reply_markup=kb
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        
        await state.set_state(BookingStates.date)

    @dp.callback_query(BookingStates.date, F.data.startswith("date_"))
    async def select_date(callback: types.CallbackQuery, state: FSMContext) -> None:
        """
        Обработать выбор даты и показать доступные временные слоты.
        
        Парсит дату из callback_data, загружает свободные слоты на эту дату
        и предлагает выбрать время.
        """
        date_str = callback.data.replace("date_", "")
        
        try:
            chosen_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception as e:
            logging.error(f"Ошибка парсинга даты: {e}")
            await callback.message.answer("Ошибка даты. Попробуйте снова.")
            return
        
        await state.update_data(date=chosen_date)
        
        # Получаем свободные слоты на выбранную дату
        slots = await get_available_slots(chosen_date)
        if not slots:
            try:
                await callback.message.edit_text(
                    "⚠️ На эту дату слоты закончились."
                )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
            return
        
        # Создаём клавиатуру с временными слотами
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=time, callback_data=f"time_{time}")]
                for time in slots
            ]
        )
        
        try:
            await callback.message.edit_text(
                "⏰ Выберите время:",
                reply_markup=kb
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        
        await state.set_state(BookingStates.time)

    @dp.callback_query(BookingStates.time, F.data.startswith("time_"))
    async def select_time(callback: types.CallbackQuery, state: FSMContext) -> None:
        """
        Обработать выбор времени и показать окончательное подтверждение.
        
        Парсит время, формирует полную дату/время записи и запрашивает
        финальное подтверждение у клиента.
        """
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
        
        # Формируем строку с датой и временем для отображения
        dt_str = datetime.combine(
            data["date"],
            chosen_time
        ).strftime('%d.%m.%Y %H:%M')
        
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
        """
        Подтвердить запись и сохранить в базу данных.
        
        Создаёт или обновляет клиента в БД, создаёт запись на приём.
        Отправляет подтверждение клиенту.
        """
        data = await state.get_data()
        
        try:
            appointment_dt = datetime.combine(data["date"], data["time"])
        except Exception as e:
            logging.error(f"Ошибка при формировании даты и времени: {e}")
            await callback.message.answer(
                "Ошибка даты/времени. Попробуйте снова."
            )
            return
        
        # Сохраняем запись в базу данных
        async for session in get_session():
            # Ищем или создаём клиента
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
                # Создаём нового клиента
                client = Client(
                    full_name=data["full_name"],
                    phone_number=data["phone"],
                    telegram_id=callback.from_user.id
                )
                session.add(client)
                await session.commit()
                await session.refresh(client)
            elif client.telegram_id is None:
                # Обновляем telegram_id для существующего клиента
                client.telegram_id = callback.from_user.id
                await session.commit()
            
            # Создаём запись на приём
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
            await callback.message.edit_text(
                "✅ Запись сохранена! Мы напомним вам за 24 часа."
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        
        await state.clear()

    @dp.callback_query(BookingStates.confirm, F.data == "confirm_no")
    async def cancel_booking(callback: types.CallbackQuery, state: FSMContext) -> None:
        """
        Отменить процесс записи на финальном этапе.
        
        Очищает состояние FSM и информирует пользователя об отмене.
        """
        try:
            await callback.message.edit_text(
                "❌ Вы отменили запись. Если передумаете — начните снова."
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        
        await state.clear()