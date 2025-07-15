from datetime import datetime, timedelta, time, date
from database.session import SessionLocal
from database.models import WorkSchedule, UnavailableSlot, Appointment
from sqlalchemy import select, and_

# 📅 Получение доступных дней
async def get_available_days(days_ahead: int = 10) -> list[tuple[str, date]]:
    today = date.today()
    results = []

    async with SessionLocal() as session:
        for offset in range(days_ahead):
            check_date = today + timedelta(days=offset)
            weekday = check_date.weekday()

            # Получаем расписание
            sched_q = await session.execute(
                select(WorkSchedule).where(WorkSchedule.weekday == weekday)
            )
            sched = sched_q.scalar()
            if not sched:
                continue

            slots = await get_available_slots(check_date)
            if slots:
                label = f"{check_date.strftime('%a, %d %b')} — {len(slots)} слотов"
                results.append((label, check_date))

    return results

# ⏰ Получение доступных слотов
async def get_available_slots(selected_date: date) -> list[str]:
    weekday = selected_date.weekday()
    slots = []

    async with SessionLocal() as session:
        schedule_q = await session.execute(
            select(WorkSchedule).where(WorkSchedule.weekday == weekday)
        )
        schedule = schedule_q.scalar()
        if not schedule:
            return []

        start = datetime.combine(selected_date, schedule.start_time)
        end = datetime.combine(selected_date, schedule.end_time)
        now = datetime.now()

        step = timedelta(minutes=60)
        current = start

        while current < end:
            # 🔒 Исключаем слоты в прошлом (если выбран сегодня)
            if selected_date == now.date() and current.time() <= now.time():
                current += step
                continue

            # ❌ Проверяем: есть ли активная запись?
            slot_taken_q = await session.execute(
                select(Appointment).where(
                    and_(
                        Appointment.date_time == current,
                        Appointment.status == "active"
                    )
                )
            )
            if slot_taken_q.scalar():
                current += step
                continue

            # ❌ Проверяем: слот вручную закрыт?
            busy_q = await session.execute(
                select(UnavailableSlot).where(
                    and_(
                        UnavailableSlot.date_time_start <= current,
                        UnavailableSlot.date_time_end > current
                    )
                )
            )
            if busy_q.scalar():
                current += step
                continue

            # ✅ Добавляем свободный слот
            slots.append(current.strftime("%H:%M"))
            current += step

    return slots
