# admin_filter.py
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

# Список Telegram ID админов
ADMINS = {5610915553, 1838230929}  # <- сюда свои ID

class AdminFilterMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id not in ADMINS:
            # Сообщение для обычных пользователей
            if isinstance(event, Message):
                await event.answer("❌ У тебя нет доступа к этому боту.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ У тебя нет доступа к этому боту.", show_alert=True)
            return  # блокируем дальнейшую обработку

        return await handler(event, data)
