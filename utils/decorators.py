from functools import wraps
from aiogram import types
from config import PSYCHOLOGIST_ID

def psychologist_only(func):
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = (
            event.from_user.id if hasattr(event, "from_user")
            else getattr(event.message, "from_user", None).id
        )
        if user_id != PSYCHOLOGIST_ID:
            await event.answer("🚫 Доступ запрещён. Только психолог может использовать эту команду.")
            return
        return await func(event, *args, **kwargs)
    return wrapper
