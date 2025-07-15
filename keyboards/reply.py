from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 🔧 Главное меню для психолога
def schedule_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🕰 Редактировать рабочее расписание")],
            [KeyboardButton(text="🗓 Указать недоступное время")],
            [KeyboardButton(text="📋 Показать записи")],
            [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )


# 📆 Выбор дня недели (для FSM)
def weekdays_keyboard():
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

# 👤 Главное меню клиента
def client_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться"), KeyboardButton(text="🗓 Мои записи")],
            [KeyboardButton(text="ℹ️ О боте")]
        ],
        resize_keyboard=True
    )
