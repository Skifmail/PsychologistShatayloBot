from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from config import PSYCHOLOGIST_ID
from keyboards.reply import schedule_main_keyboard
from handlers.psychologist.records import choose_records_filter
from handlers.psychologist.schedule import view_schedule
from handlers.psychologist.work_hours import edit_work_schedule

# 📋 Команда /psych — меню психолога
async def open_psychologist_menu(message: types.Message):
    if message.from_user.id != PSYCHOLOGIST_ID:
        await message.answer("🚫 Доступ запрещён. Это меню только для психолога.")
        return
    await message.answer("📋 Меню психолога:", reply_markup=schedule_main_keyboard())

# 🔙 Назад — только для психолога
async def back_to_psychologist_menu(message: types.Message):
    await message.answer("↩️ Вы вернулись в меню психолога.", reply_markup=schedule_main_keyboard())

# 🔗 Регистрация хэндлеров психолога
def register_psychologist_menu(dp: Dispatcher):
    dp.message.register(open_psychologist_menu, Command("psych"))
    dp.message.register(back_to_psychologist_menu, F.text == "🔙 Назад", lambda msg: msg.from_user.id == PSYCHOLOGIST_ID)
    dp.message.register(choose_records_filter, F.text == "📋 Показать записи")
    dp.message.register(view_schedule, F.text == "📆 Расписание")
    dp.message.register(edit_work_schedule, F.text == "🕰 Редактировать рабочее расписание")
