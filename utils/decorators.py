"""
Декораторы для ограничения доступа к командам (только для психолога).
"""
from functools import wraps
from aiogram import types
from config import PSYCHOLOGIST_ID
from typing import Callable, Awaitable, Any

def psychologist_only(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Декоратор: разрешает выполнение только психологу."""
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = None
        if hasattr(event, "from_user") and getattr(event.from_user, "id", None) is not None:
            user_id = event.from_user.id
        elif hasattr(event, "message") and hasattr(event.message, "from_user") and getattr(event.message.from_user, "id", None) is not None:
            user_id = event.message.from_user.id
        if user_id != PSYCHOLOGIST_ID:
            await event.answer("🚫 Доступ запрещён. Только психолог может использовать эту команду.")
            return
        return await func(event, *args, **kwargs)
    return wrapper
