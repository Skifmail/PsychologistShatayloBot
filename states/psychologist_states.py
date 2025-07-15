from aiogram.fsm.state import StatesGroup, State

class DateQueryState(StatesGroup):
    date = State()

class WorkHoursStates(StatesGroup):
    """FSM: Добавление разового рабочего дня по дате"""
    date = State()
    start_time = State()
    end_time = State()

class ScheduleStates(StatesGroup):
    """FSM: Закрытие времени вручную (недоступность)"""
    date = State()
    start_time = State()
    end_time = State()

class WorkScheduleStates(StatesGroup):
    """FSM: Задание типового графика по дням недели"""
    day = State()
    start_time = State()
    end_time = State()
