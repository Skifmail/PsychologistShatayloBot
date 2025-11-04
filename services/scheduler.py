"""
Планировщик автоматических напоминаний и уведомлений.

Управляет отправкой напоминаний клиентам о предстоящих записях
и ежедневным дайджестом для психолога. Использует APScheduler
для планирования задач.
"""
import logging
from datetime import datetime, timedelta, time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from database.session import get_session
from database.models import Appointment, Client
from config import PSYCHOLOGIST_ID

scheduler = AsyncIOScheduler()


async def send_missed_day_reminders(bot: Bot) -> None:
    """
    Отправить пропущенные напоминания о записях на сегодня.
    
    Вызывается при запуске бота для отправки напоминаний
    о записях на сегодня, если бот был выключен.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
    """
    async for session in get_session():
        now = datetime.now()
        today = now.date()
        query = await session.execute(
            select(Appointment).where(
                Appointment.date_time >= datetime.combine(today, datetime.min.time()),
                Appointment.date_time <= datetime.combine(today, datetime.max.time()),
                Appointment.status.in_(["active", "confirmed"]),
                Appointment.confirmed == None
            ).order_by(Appointment.date_time)
        )
        appointments = query.scalars().all()
        for appointment in appointments:
            if appointment.date_time <= now:
                continue
            client = await session.get(Client, appointment.client_id)
            if not client or not getattr(client, 'telegram_id', None):
                continue
            msg = (
                f"👋 Напоминаем:\n"
                f"Сегодня у вас запись в <b>{appointment.date_time.strftime('%H:%M')}</b>.\n"
                f"Пожалуйста, подтвердите, что всё в силе."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{appointment.id}_yes")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=f"confirm_{appointment.id}_no")]
            ])
            try:
                await bot.send_message(chat_id=client.telegram_id, text=msg, reply_markup=kb, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Ошибка отправки напоминания клиенту: {e}")

async def send_reminder(bot: Bot, appointment_id: int) -> None:
    """
    Отправить напоминание клиенту за 24 часа до записи.
    
    Отправляет сообщение с кнопками подтверждения/отмены записи.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
        appointment_id: ID записи для напоминания
    """
    async for session in get_session():
        appointment = await session.get(Appointment, appointment_id)
        if not appointment or appointment.confirmed is not None:
            return
        client = await session.get(Client, appointment.client_id)
        if not client or not getattr(client, 'telegram_id', None):
            return
        msg = (
            f"📅 Напоминание:\n"
            f"Вы записаны на <b>{appointment.date_time.strftime('%d.%m.%Y в %H:%M')}</b>\n"
            f"Подтвердите, пожалуйста своё посещение."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{appointment.id}_yes")],
            [InlineKeyboardButton(text="❌ Нет", callback_data=f"confirm_{appointment.id}_no")]
        ])
        try:
            await bot.send_message(chat_id=client.telegram_id, text=msg, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ошибка отправки напоминания клиенту: {e}")

async def send_day_of_reminder(bot: Bot, appointment_id: int) -> None:
    """
    Отправить утреннее напоминание в день приёма.
    
    Отправляется в 7:30 утра в день записи.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
        appointment_id: ID записи для напоминания
    """
    async for session in get_session():
        appointment = await session.get(Appointment, appointment_id)
        if not appointment:
            return
        client = await session.get(Client, appointment.client_id)
        if not client or not getattr(client, 'telegram_id', None):
            return
        msg = (
            f"👋 Напоминаем:\n"
            f"Сегодня у вас запись в <b>{appointment.date_time.strftime('%H:%M')}</b>.\n"
            f"Пожалуйста, подтвердите, что всё в силе."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{appointment.id}_yes")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"confirm_{appointment.id}_no")]
        ])
        try:
            await bot.send_message(chat_id=client.telegram_id, text=msg, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ошибка отправки утреннего напоминания клиенту: {e}")

async def send_daily_digest(bot: Bot) -> None:
    """
    Отправить утренний дайджест психологу.
    
    Формирует сводку всех записей на сегодня с отметками
    о подтверждении клиентами. Отправляется в 7:30 утра.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
    """
    async for session in get_session():
        today = datetime.now().date()
        query = await session.execute(
            select(Appointment).where(
                Appointment.date_time >= datetime.combine(today, datetime.min.time()),
                Appointment.date_time <= datetime.combine(today, datetime.max.time()),
                Appointment.status.in_(["active", "confirmed"])
            ).order_by(Appointment.date_time)
        )
        appointments = query.scalars().all()
        if not appointments:
            await bot.send_message(chat_id=PSYCHOLOGIST_ID, text="📭 Сегодня нет приёмов.")
            return
        lines = []
        for app in appointments:
            client = await session.get(Client, app.client_id)
            name = getattr(client, 'full_name', 'Неизвестный') if client else 'Неизвестный'
            confirm_icon = "✅" if app.confirmed else "❓"
            time_str = app.date_time.strftime("%H:%M")
            lines.append(f"• {time_str} — {name} {confirm_icon}")
        summary = f"🧠 <b>Сегодня у вас {len(appointments)} приёмов:</b>\n\n" + "\n".join(lines)
        try:
            await bot.send_message(chat_id=PSYCHOLOGIST_ID, text=summary, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ошибка отправки дайджеста психологу: {e}")

def schedule_reminders(bot: Bot) -> None:
    """
    Запустить планировщик напоминаний.
    
    Инициализирует APScheduler и настраивает задачи:
    - Проверка записей для напоминаний за 24 часа (каждый час)
    - Проверка записей для утренних напоминаний
    - Ежедневный дайджест для психолога (7:30)
    
    Args:
        bot: Экземпляр бота для передачи в задачи
    """
    async def planner():
        async for session in get_session():
            now = datetime.now()
            # Напоминания за 24 часа
            in_24h_range_start = now + timedelta(hours=24)
            in_24h_range_end = in_24h_range_start + timedelta(minutes=1)
            query_24h = await session.execute(
                select(Appointment).where(
                    Appointment.date_time.between(in_24h_range_start, in_24h_range_end),
                    Appointment.status.in_(["active", "confirmed"]),
                    Appointment.confirmed == None
                )
            )
            for appointment in query_24h.scalars().all():
                scheduler.add_job(
                    send_reminder,
                    args=[bot, appointment.id],
                    trigger="date",
                    run_date=in_24h_range_start
                )
            # Утренние напоминания в день приёма
            today = now.date()
            query_today = await session.execute(
                select(Appointment).where(
                    Appointment.date_time >= datetime.combine(today, datetime.min.time()),
                    Appointment.date_time <= datetime.combine(today, datetime.max.time()),
                    Appointment.status.in_(["active", "confirmed"]),
                    Appointment.confirmed == None
                )
            )
            for appointment in query_today.scalars().all():
                run_time = datetime.combine(today, time(hour=7, minute=30))
                if run_time > now:
                    scheduler.add_job(
                        send_day_of_reminder,
                        args=[bot, appointment.id],
                        trigger="date",
                        run_date=run_time
                    )
        scheduler.add_job(
            send_daily_digest,
            args=[bot],
            trigger="cron",
            hour=7,
            minute=30
        )
    scheduler.add_job(planner, "interval", minutes=60)
    scheduler.start()
