from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, time
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.session import SessionLocal
from database.models import Appointment, Client
from sqlalchemy import select
from config import PSYCHOLOGIST_ID

scheduler = AsyncIOScheduler()

async def send_missed_day_reminders(bot: Bot):
    async with SessionLocal() as session:
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
                continue  # ❌ уже прошло — не напоминать

            client = await session.get(Client, appointment.client_id)
            if not client or not client.telegram_id:
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
            await bot.send_message(chat_id=client.telegram_id, text=msg, reply_markup=kb, parse_mode="HTML")



# 🔔 Напоминание за 24 часа
async def send_reminder(bot: Bot, appointment_id: int):
    async with SessionLocal() as session:
        appointment = await session.get(Appointment, appointment_id)
        if not appointment or appointment.confirmed is not None:
            return

        client = await session.get(Client, appointment.client_id)
        if not client or not client.telegram_id:
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
        await bot.send_message(chat_id=client.telegram_id, text=msg, reply_markup=kb, parse_mode="HTML")

# 🔔 Утреннее напоминание в день приёма
async def send_day_of_reminder(bot: Bot, appointment_id: int):
    async with SessionLocal() as session:
        appointment = await session.get(Appointment, appointment_id)
        if not appointment:
            return

        client = await session.get(Client, appointment.client_id)
        if not client or not client.telegram_id:
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
        await bot.send_message(chat_id=client.telegram_id, text=msg, reply_markup=kb, parse_mode="HTML")

# 🧠 Ежедневная сводка для психолога
async def send_daily_digest(bot: Bot):
    async with SessionLocal() as session:
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
            name = client.full_name if client else "Неизвестный"
            confirm_icon = "✅" if app.confirmed else "❓"
            time_str = app.date_time.strftime("%H:%M")
            lines.append(f"• {time_str} — {name} {confirm_icon}")

        summary = f"🧠 <b>Сегодня у вас {len(appointments)} приёмов:</b>\n\n" + "\n".join(lines)
        await bot.send_message(chat_id=PSYCHOLOGIST_ID, text=summary, parse_mode="HTML")

# ⏰ Планирование
def schedule_reminders(bot: Bot):
    async def planner():
        async with SessionLocal() as session:
            now = datetime.now()

            # 🔔 Напоминания за 24 часа
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

            # ☀️ Утренние напоминания в день приёма
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
                run_time = datetime.combine(today, time(hour=7, minute=5))
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
            minute=0
        )

    scheduler.add_job(planner, "interval", minutes=60)
    scheduler.start()
