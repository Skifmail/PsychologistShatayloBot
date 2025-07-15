# states/client_states.py

from aiogram.fsm.state import StatesGroup, State

class BookingStates(StatesGroup):
    full_name = State()
    phone = State()
    service = State()
    date = State()
    time = State()
    confirm = State()
    reschedule = State()  # 👈 новое состояние для переноса
