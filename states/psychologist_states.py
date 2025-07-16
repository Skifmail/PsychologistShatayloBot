"""
FSM-состояния для психолога: выбор даты, редактирование рабочих часов, ручное закрытие слотов, типовой график.
"""
from aiogram.fsm.state import StatesGroup, State

class DateQueryState(StatesGroup):
    """FSM: выбор даты для просмотра записей."""
    date: State = State()

class WorkHoursStates(StatesGroup):
    """FSM: добавление разового рабочего дня по дате."""
    date: State = State()
    start_time: State = State()
    end_time: State = State()

class ScheduleStates(StatesGroup):
    """FSM: закрытие времени вручную (недоступность)."""
    date: State = State()
    start_time: State = State()
    end_time: State = State()

class WorkScheduleStates(StatesGroup):
    """FSM: задание типового графика по дням недели."""
    day: State = State()
    start_time: State = State()
    end_time: State = State()

class ManualBookingStates(StatesGroup):
    date = State()
    time = State()
    full_name = State()
    phone = State()
    confirm = State()
