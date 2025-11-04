"""
Декораторы для контроля доступа к функциям бота.

Предоставляет декораторы для ограничения доступа к определённым
командам и обработчикам только для авторизованных пользователей.
"""
from functools import wraps
from typing import Callable, Awaitable, Any

from config import PSYCHOLOGIST_ID


def psychologist_only(
    func: Callable[..., Awaitable[Any]]
) -> Callable[..., Awaitable[Any]]:
    """
    Декоратор для ограничения доступа к функции только психологу.
    
    Проверяет Telegram ID пользователя, вызвавшего команду/callback.
    Если ID не совпадает с PSYCHOLOGIST_ID из конфигурации, отправляет
    сообщение об отказе в доступе и прерывает выполнение функции.
    
    Args:
        func: Асинхронная функция-обработчик для защиты
        
    Returns:
        Callable: Обёрнутая функция с проверкой доступа
        
    Example:
        ```python
        @psychologist_only
        async def view_schedule(message: types.Message) -> None:
            # Эта функция доступна только психологу
            ...
        ```
    """
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = None
        
        # Попытка получить user_id из разных типов событий
        if hasattr(event, "from_user") and \
           getattr(event.from_user, "id", None) is not None:
            user_id = event.from_user.id
        elif hasattr(event, "message") and \
             hasattr(event.message, "from_user") and \
             getattr(event.message.from_user, "id", None) is not None:
            user_id = event.message.from_user.id
        
        # Проверка доступа
        if user_id != PSYCHOLOGIST_ID:
            await event.answer(
                "🚫 Доступ запрещён. Только психолог может использовать эту команду."
            )
            return
        
        return await func(event, *args, **kwargs)
    
    return wrapper
