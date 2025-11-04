"""
Обработчики подтверждения записей через inline-кнопки.

Обрабатывает ответы клиентов на напоминания (подтверждение или отказ от записи).
Уведомляет психолога о решении клиента.
"""
import logging

from aiogram import Dispatcher, types, F
from sqlalchemy import select

from database.session import get_session
from database.models import Appointment, Client
from config import PSYCHOLOGIST_ID


def register_reminder_handlers(dp: Dispatcher) -> None:
    """
    Зарегистрировать обработчики подтверждения/отмены записей.
    
    Обрабатывает callback от inline-кнопок в напоминаниях.
    
    Args:
        dp: Диспетчер aiogram для регистрации обработчиков
    """
    @dp.callback_query(F.data.startswith("confirm_"))
    async def handle_confirmation(callback: types.CallbackQuery) -> None:
        """
        Обработать ответ клиента на напоминание.
        
        Парсит callback_data, обновляет статус подтверждения записи в БД,
        отправляет уведомление психологу о решении клиента.
        """
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
