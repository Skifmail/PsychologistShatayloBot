"""
FSM-состояния для процесса записи клиента.

Определяет последовательность состояний конечного автомата (FSM)
при записи клиента на приём и переносе существующей записи.
"""
from aiogram.fsm.state import StatesGroup, State


class BookingStates(StatesGroup):
    """
    Состояния процесса записи клиента к психологу.
    
    Attributes:
        full_name: Ввод полного имени клиента (ФИО)
        phone: Ввод номера телефона клиента
        service: Выбор типа услуги (консультация, первая встреча, супервизия)
        date: Выбор даты приёма
        time: Выбор времени приёма
        confirm: Подтверждение записи
        reschedule: Процесс переноса существующей записи
    """
    full_name: State = State()
    phone: State = State()
    service: State = State()
    date: State = State()
    time: State = State()
    confirm: State = State()
    reschedule: State = State()
