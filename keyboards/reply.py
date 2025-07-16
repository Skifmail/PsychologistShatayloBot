"""
Reply-клавиатуры для клиента и психолога.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional

def schedule_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню для психолога."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗰 Редактировать рабочее расписание")],
            [KeyboardButton(text="🗓 Указать недоступное время")],
            [KeyboardButton(text="📋 Показать записи")],
            [KeyboardButton(text="🔎 Посмотреть свободные слоты")],
            [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def weekdays_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора дня недели для FSM."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Понедельник"), KeyboardButton(text="Вторник")],
            [KeyboardButton(text="Среда"), KeyboardButton(text="Четверг")],
            [KeyboardButton(text="Пятница"), KeyboardButton(text="Суббота")],
            [KeyboardButton(text="Воскресенье")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def client_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню для клиента."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться"), KeyboardButton(text="🗓 Мои записи")],
            [KeyboardButton(text="ℹ️ О боте")]
        ],
        resize_keyboard=True
    )




# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
#
# # 🔧 Главное меню для психолога
# def schedule_main_keyboard():
#     return ReplyKeyboardMarkup(
#         keyboard=[
#             [KeyboardButton(text="🕰 Редактировать рабочее расписание")],
#             [KeyboardButton(text="🗓 Указать недоступное время")],
#             [KeyboardButton(text="📋 Показать записи")],
#             [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="🔙 Назад")]
#         ],
#         resize_keyboard=True
#     )
#
#
# # 📆 Выбор дня недели (для FSM)
# def weekdays_keyboard():
#     return ReplyKeyboardMarkup(
#         keyboard=[
#             [KeyboardButton(text="Понедельник"), KeyboardButton(text="Вторник")],
#             [KeyboardButton(text="Среда"), KeyboardButton(text="Четверг")],
#             [KeyboardButton(text="Пятница"), KeyboardButton(text="Суббота")],
#             [KeyboardButton(text="Воскресенье")],
#             [KeyboardButton(text="🔙 Назад")]
#         ],
#         resize_keyboard=True
#     )
#
# # 👤 Главное меню клиента
# def client_main_keyboard():
#     return ReplyKeyboardMarkup(
#         keyboard=[
#             [KeyboardButton(text="📅 Записаться"), KeyboardButton(text="🗓 Мои записи")],
#             [KeyboardButton(text="ℹ️ О боте")]
#         ],
#         resize_keyboard=True
#     )
