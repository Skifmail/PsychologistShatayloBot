"""
FSM-состояния для записи клиента (имя, телефон, услуга, дата, время, подтверждение, перенос).
"""
from aiogram.fsm.state import StatesGroup, State

class BookingStates(StatesGroup):
    """Состояния FSM для записи клиента."""
    full_name: State = State()
    phone: State = State()
    service: State = State()
    date: State = State()
    time: State = State()
    confirm: State = State()
    reschedule: State = State()  # новое состояние для переноса




# # states/client_states.py
#
# from aiogram.fsm.state import StatesGroup, State
#
# class BookingStates(StatesGroup):
#     full_name = State()
#     phone = State()
#     service = State()
#     date = State()
#     time = State()
#     confirm = State()
#     reschedule = State()  # 👈 новое состояние для переноса
