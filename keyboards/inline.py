"""
Inline-клавиатуры для интерактивного взаимодействия.

Содержит функции для создания inline-клавиатур, которые отображаются
под сообщениями бота и позволяют пользователю выбирать опции.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def service_keyboard() -> InlineKeyboardMarkup:
    """
    Создать клавиатуру выбора типа услуги.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками для выбора услуги:
            - Консультация (service_consult)
            - Первая встреча (service_intro)
            - Супервизия (service_supervision)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🧠 Консультация",
            callback_data="service_consult"
        )],
        [InlineKeyboardButton(
            text="💬 Первая встреча",
            callback_data="service_intro"
        )],
        [InlineKeyboardButton(
            text="📌 Супервизия",
            callback_data="service_supervision"
        )],
    ])


def confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Создать клавиатуру подтверждения действия.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками:
            - Подтвердить (confirm_yes)
            - Отменить (confirm_no)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data="confirm_yes"
        )],
        [InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="confirm_no"
        )],
    ])
