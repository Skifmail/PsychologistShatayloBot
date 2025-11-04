"""
FSM-состояния для функций психолога.

Определяет последовательности состояний конечного автомата (FSM)
для различных операций, доступных психологу: просмотр записей,
настройка расписания, блокировка слотов, ручная запись клиентов.
"""
from aiogram.fsm.state import StatesGroup, State


class DateQueryState(StatesGroup):
    """
    Состояния для выбора даты просмотра записей.
    
    Attributes:
        date: Ввод даты для фильтрации записей
    """
    date: State = State()


class WorkHoursStates(StatesGroup):
    """
    Состояния для добавления разового рабочего дня.
    
    Используется для добавления нестандартных рабочих часов
    на конкретную дату (не входящую в регулярное расписание).
    
    Attributes:
        date: Ввод даты рабочего дня
        start_time: Ввод времени начала работы
        end_time: Ввод времени окончания работы
    """
    date: State = State()
    start_time: State = State()
    end_time: State = State()


class ScheduleStates(StatesGroup):
    """
    Состояния для ручного закрытия временных слотов.
    
    Используется психологом для блокировки времени
    (отпуск, личные дела, внешние встречи).
    
    Attributes:
        date: Ввод даты недоступности
        start_time: Ввод времени начала недоступности
        end_time: Ввод времени окончания недоступности
    """
    date: State = State()
    start_time: State = State()
    end_time: State = State()


class WorkScheduleStates(StatesGroup):
    """
    Состояния для настройки регулярного расписания.
    
    Используется для задания рабочих часов по дням недели.
    
    Attributes:
        day: Выбор дня недели
        start_time: Ввод времени начала рабочего дня
        end_time: Ввод времени окончания рабочего дня
    """
    day: State = State()
    start_time: State = State()
    end_time: State = State()


class ManualBookingStates(StatesGroup):
    """
    Состояния для ручной записи клиента психологом.
    
    Позволяет психологу самостоятельно добавить запись клиента
    (например, при записи по телефону).
    
    Attributes:
        date: Ввод даты записи
        time: Выбор времени записи
        full_name: Ввод ФИО клиента
        phone: Ввод телефона клиента
        confirm: Подтверждение создания записи
    """
    date = State()
    time = State()
    full_name = State()
    phone = State()
    confirm = State()
