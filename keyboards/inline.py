"""
Inline-клавиатуры для взаимодействия с пользователем (выбор услуги, подтверждение).
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional

def service_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора услуги для записи."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Консультация", callback_data="service_consult")],
        [InlineKeyboardButton(text="💬 Первая встреча", callback_data="service_intro")],
        [InlineKeyboardButton(text="📌 Супервизия", callback_data="service_supervision")],
    ])

def confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения/отмены записи."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_no")],
    ])
