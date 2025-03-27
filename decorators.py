import inspect
import logging
from typing import cast, Optional
from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

class MessageManager:
    def __init__(self):
        self.message_stack = []
        self.last_user_message: Optional[int] = None

    async def cleanup(self, bot: Bot, chat_id: int):
        if self.last_user_message:
            try:
                await bot.delete_message(chat_id, self.last_user_message)
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения: {e}")

        for msg_id in self.message_stack:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception as e:
                if "message to delete not found" not in str(e):
                    logger.error(f"Ошибка удаления: {e}")
        self.message_stack.clear()
        self.last_user_message = None

    def track(self, message: Message):
        self.message_stack.append(message.message_id)

def message_cleaner(func):
    async def wrapper(*args, **kwargs):
        filtered_kwargs = {
            k: v for k, v in kwargs.items()
            if k in inspect.signature(func).parameters
        }

        state = None
        for arg in args:
            if isinstance(arg, FSMContext):
                state = arg
                break
        state = filtered_kwargs.get('state', state)

        data = await state.get_data() if state else {}
        manager: MessageManager = data.get('manager', MessageManager())

        message = None
        callback = None
        for arg in args:
            if isinstance(arg, CallbackQuery):
                message = arg.message
                callback = arg
                break
            elif isinstance(arg, Message):
                message = arg
                break

        if message and callback and not callback.data.startswith(("copy_", "length_", "check_password_", "main_menu", "check_custom", "check_hibp")):
            try:
                await message.delete()
                manager.last_user_message = cast(int, message.message_id)
            except Exception as e:
                logger.error(f"Ошибка удаления: {e}")

        result = await func(*args, **filtered_kwargs)

        if isinstance(result, Message):
            manager.track(result)
            if state:
                await state.update_data(manager=manager)

        return result
    return wrapper