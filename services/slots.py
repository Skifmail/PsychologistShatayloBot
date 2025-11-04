"""
Сервисы для работы с временными слотами и доступными днями записи.

Модуль предоставляет функции для определения свободных дней и времени,
когда клиенты могут записаться на приём к психологу, с учётом рабочего
расписания, существующих записей и вручную закрытых слотов.
"""
from datetime import datetime, timedelta, date
from typing import List, Tuple

from sqlalchemy import select, and_

from database.session import get_session
from database.models import WorkSchedule, UnavailableSlot, Appointment


async def get_available_days(days_ahead: int = 10) -> List[Tuple[str, date]]:
    """
    Получить список доступных для записи дней.
    
    Проверяет наличие рабочего расписания и свободных слотов для каждого дня
    в указанном диапазоне. Возвращает только те дни, когда есть хотя бы один
    свободный слот для записи.
    
    Args:
        days_ahead (int): Количество дней вперёд для проверки (по умолчанию 10)
        
    Returns:
        List[Tuple[str, date]]: Список кортежей (текстовая метка, объект даты),
                                где метка содержит день недели, дату и количество
                                свободных слотов
        
    Example:
        >>> days = await get_available_days(7)
        >>> print(days)
        [('Mon, 05 Nov — 5 слотов', datetime.date(2025, 11, 5)), ...]
    """
    today = date.today()
    results = []
    async for session in get_session():
        for offset in range(days_ahead):
            check_date = today + timedelta(days=offset)
            weekday = check_date.weekday()
            
            # Проверяем наличие рабочего расписания на этот день недели
            sched_q = await session.execute(
                select(WorkSchedule).where(WorkSchedule.weekday == weekday)
            )
            sched = sched_q.scalar()
            if not sched:
                continue
            
            # Проверяем наличие свободных слотов
            slots = await get_available_slots(check_date)
            if slots:
                label = f"{check_date.strftime('%a, %d %b')} — {len(slots)} слотов"
                results.append((label, check_date))
    return results


async def get_available_slots(selected_date: date) -> List[str]:
    """
    Получить список свободных временных слотов на указанную дату.
    
    Проверяет рабочее расписание психолога на выбранный день недели,
    затем фильтрует слоты с учётом:
    - Прошедшего времени (если дата = сегодня)
    - Существующих активных записей
    - Вручную заблокированных слотов (отпуск, личные дела)
    
    Args:
        selected_date (date): Дата для проверки доступных слотов
        
    Returns:
        List[str]: Список строк с доступным временем в формате "HH:MM"
        
    Example:
        >>> slots = await get_available_slots(date(2025, 11, 5))
        >>> print(slots)
        ['10:00', '11:00', '14:00', '15:00']
    """
    weekday = selected_date.weekday()
    slots = []
    
    async for session in get_session():
        # Получаем рабочее расписание для данного дня недели
        schedule_q = await session.execute(
            select(WorkSchedule).where(WorkSchedule.weekday == weekday)
        )
        schedule = schedule_q.scalar()
        if not schedule:
            return []
        
        start = datetime.combine(selected_date, schedule.start_time)
        end = datetime.combine(selected_date, schedule.end_time)
        now = datetime.now()
        step = timedelta(minutes=60)  # Слоты по 60 минут
        current = start
        
        while current < end:
            # Пропускаем слоты в прошлом (если выбран сегодня)
            if selected_date == now.date() and current.time() <= now.time():
                current += step
                continue
            
            # Проверяем наличие активной записи на это время
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
            
            # Проверяем вручную закрытые слоты
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
            
            # Слот свободен — добавляем в список
            slots.append(current.strftime("%H:%M"))
            current += step
    
    return slots
