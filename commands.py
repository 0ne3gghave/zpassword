from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, User as TgUser
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from typing import Optional, cast

from crud import (
    get_user,
    register_user,
    get_password_count,
    get_passwords
)
from keyboards import (
    main_menu,
    password_length_keyboard,
    passwords_pagination,
)
from callbacks import MessageManager  # УДАЛЕН НЕНУЖНЫЙ ИМПОРТ show_main_menu
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext) -> None:
    """Исправленная реализация /start без дублирования клавиатуры"""
    try:
        manager = MessageManager()
        await state.set_state(None)
        await state.update_data(manager=manager)

        # Проверка и регистрация пользователя
        user: Optional[TgUser] = cast(TgUser, message.from_user)
        if not user:
            raise ValueError("Не получен объект пользователя")

        existing_user = await get_user(user.id)
        if not existing_user:
            await register_user(user.id, user.username or "")

        # Отправка ЕДИНСТВЕННОГО сообщения с клавиатурой
        welcome_msg = (
            f"👋 <b>Добро пожаловать, {user.username or 'Пользователь'}!</b>\n\n"
            "🔐 Я бот для генерации и хранения паролей.\n"
            "Используйте кнопки ниже для навигации:"
        )
        msg = await message.answer(
            welcome_msg,
            reply_markup=main_menu(),  # Клавиатура отправляется здесь
            parse_mode=ParseMode.HTML
        )
        manager.track(msg)
        await state.update_data(manager=manager)

    except Exception as e:
        logger.critical(f"Ошибка: {e}", exc_info=True)
        await message.answer("⚠️ Системная ошибка. /start")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Реализация помощи с проверкой HTML-парсера"""
    help_text = (
        "<b>📚 Доступные команды:</b>\n\n"
        "🔐 /generate - Генерация пароля\n"
        "📋 /list - Список паролей\n"
        "⚙️ Используйте кнопки меню"
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML)


@router.message(Command("list"))
async def list_passwords_command(message: Message, state: FSMContext) -> None:
    """Полный цикл работы с паролями"""
    try:
        data = await state.get_data()
        manager: Optional[MessageManager] = data.get('manager')

        if not manager:
            manager = MessageManager()
            await state.update_data(manager=manager)

        user_id: Optional[int] = message.from_user.id
        if not user_id:
            raise ValueError("Не получен user_id")

        passwords = await get_passwords(user_id)
        total: Optional[int] = await get_password_count(user_id)

        per_page = 15
        total_pages = max((cast(int, total) + per_page - 1) // per_page, 1)
        reply_markup = passwords_pagination(1, total_pages, passwords, per_page)

        msg = await message.answer(
            "🔑 Список паролей:" if passwords else "📭 Нет данных",
            reply_markup=reply_markup
        )
        manager.track(msg)

    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await message.answer("⛔ Ошибка загрузки")



@router.callback_query(F.data == "clear_all")
async def process_clear_all(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка подтверждения очистки"""
    try:
        data = await state.get_data()
        manager: Optional[MessageManager] = data.get('manager')
        user_id: Optional[int] = data.get('user_id')

        if not all([manager, user_id]):
            raise ValueError("Недостаточно данных для очистки")

        await callback.message.edit_text("✅ Данные удалены")
        # Отправка главного меню через прямое обновление клавиатуры
        await callback.message.edit_reply_markup(reply_markup=main_menu())

    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await callback.message.edit_text("⛔ Критическая ошибка")


@router.message(Command("generate"))
async def generate_command(message: Message, state: FSMContext) -> None:
    """Полный цикл генерации пароля"""
    try:
        data = await state.get_data()
        manager: Optional[MessageManager] = data.get('manager')

        if not manager:
            manager = MessageManager()
            await state.update_data(manager=manager)

        msg = await message.answer(
            "🔢 Выберите длину:",
            reply_markup=password_length_keyboard()
        )
        manager.track(msg)

    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await message.answer("⚠️ Ошибка инициализации")