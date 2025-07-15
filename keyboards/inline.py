# keyboards/inline.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def service_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Консультация", callback_data="service_consult")],
        [InlineKeyboardButton(text="💬 Первая встреча", callback_data="service_intro")],
        [InlineKeyboardButton(text="📌 Супервизия", callback_data="service_supervision")],
    ])

def confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_no")],
    ])
