import logging
from typing import cast
from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup

from decorators import message_cleaner, MessageManager
from crud import (
    save_password,
    get_passwords,
    get_password_count,
    delete_password,
    get_user,
    register_user
)
from keyboards import (
    main_menu,
    password_length_keyboard,
    passwords_pagination,
    after_generation_keyboard
)
from password import generate_password, estimate_crack_time
from security import calculate_password_strength, check_hibp

logger = logging.getLogger(__name__)
router = Router()

class HIBPCheckStates(StatesGroup):
    AWAITING_HIBP_PASSWORD = State()

@router.callback_query(F.data == "generate")
@message_cleaner
async def handle_generate(callback: CallbackQuery, state: FSMContext):
    manager = MessageManager()
    msg = await callback.message.answer(
        "🔢 Выберите длину пароля:",
        reply_markup=password_length_keyboard()
    )
    manager.track(msg)
    await state.update_data(manager=manager)

@router.callback_query(F.data.startswith("length_"))
@message_cleaner
async def process_password(callback: CallbackQuery, state: FSMContext):
    length = int(callback.data.split("_")[1])
    password = generate_password(str(length))
    user_id = callback.from_user.id

    await state.update_data(last_length=length)

    if not await get_user(user_id):
        await register_user(user_id, callback.from_user.username or "")

    try:
        await save_password(user_id, password)
        await callback.message.edit_text(
            f"🔐 Ваш пароль:\n<code>{password}</code>",
            parse_mode="HTML",
            reply_markup=after_generation_keyboard(password, length)
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        await callback.answer("⚠️ Ошибка генерации")

@router.callback_query(F.data.startswith("copy_"))
async def copy_password(callback: CallbackQuery, bot: Bot):
    password = callback.data.split("_", 1)[1]
    try:
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"📋 Скопируйте ваш пароль:\n<code>{password}</code>",
            parse_mode=ParseMode.HTML
        )
        await callback.answer("✅ Успешно скопировано!", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка копирования: {e}")
        await callback.answer("⚠️ Ошибка копирования", show_alert=True)

@router.callback_query(F.data.startswith("delete_"))
@message_cleaner
async def delete_password_handler(callback: CallbackQuery, state: FSMContext):
    password_id = int(callback.data.split("_")[1])
    if await delete_password(password_id):
        await callback.answer("🗑️ Удалено!", show_alert=True)
        await show_passwords_list(callback, state)
    else:
        await callback.answer("⚠️ Ошибка", show_alert=True)

@router.callback_query(F.data == "pswd_list")
@message_cleaner
async def show_passwords_list(callback: CallbackQuery, state: FSMContext):
    user_id = cast(int, callback.from_user.id)
    try:
        total = await get_password_count(user_id)
        per_page = 15
        total_pages = max((total + per_page - 1) // per_page, 1)
        passwords = await get_passwords(user_id, 1, per_page)

        msg = await callback.message.answer(
            "🔑 Список паролей:",
            reply_markup=passwords_pagination(1, total_pages, passwords, per_page)
        )
        data = await state.get_data()
        if 'manager' in data:
            data['manager'].track(msg)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("⛔ Ошибка загрузки")

@router.callback_query(F.data == "main_menu")
@message_cleaner
async def return_to_main(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "🏠 Главное меню:",
            reply_markup=main_menu()
        )
        await state.clear()
    except Exception as e:
        await callback.message.answer(
            "🏠 Главное меню:",
            reply_markup=main_menu()
        )

@router.callback_query(F.data.startswith("regenerate_"))
@message_cleaner
async def regenerate_password(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        length = data.get('last_length', 12)
        new_password = generate_password(str(length))
        user_id = callback.from_user.id

        await save_password(user_id, new_password)

        try:
            await callback.message.edit_text(
                f"🔐 Новый пароль:\n<code>{new_password}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=after_generation_keyboard(new_password, length)
            )
        except Exception:
            msg = await callback.message.answer(
                f"🔐 Новый пароль:\n<code>{new_password}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=after_generation_keyboard(new_password, length)
            )
            data = await state.get_data()
            if manager := data.get('manager'):
                manager.track(msg)

        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка регенерации: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка генерации", show_alert=True)

@router.callback_query(F.data.startswith("check_"))
@message_cleaner
async def handle_password_check(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        password = callback.data.split("_", 1)[1]
        report, recommendations = calculate_password_strength(password)
        recommendations_text = "\n".join(
            f"• {rec}" for rec in recommendations) if recommendations else "✅ Пароль соответствует базовым требованиям"

        response = (
            f"🔍 Анализ пароля:\n<code>{password}</code>\n\n"
            f"📈 Энтропия: {report['entropy']:.1f} бит\n"
            f"⚖️ Сложность: {report['score']:.1f}/100\n\n"
            f"📝 Рекомендации:\n{recommendations_text}"
        )

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        msg = await callback.message.answer(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )

        data = await state.get_data()
        manager = data.get('manager', MessageManager())
        manager.track(msg)
        await state.update_data(manager=manager)
    except Exception as e:
        logger.error(f"Ошибка проверки: {e}")
        await callback.answer("⚠️ Ошибка анализа", show_alert=True)
    finally:
        await state.clear()

@router.message(F.text)
@message_cleaner
async def handle_text_message(message: Message, state: FSMContext):
    try:
        if message.text.startswith("/"):
            await message.answer("ℹ️ Используйте кнопки меню для навигации")
            return

        password = message.text.strip()
        data = await state.get_data()
        manager = data.get("manager", MessageManager())

        report, recommendations = calculate_password_strength(password)
        recommendations_text = "\n".join(f"• {rec}" for rec in recommendations)

        response = (
            f"🔍 Анализ пароля:\n<code>{password}</code>\n\n"
            f"📈 Энтропия: {report.get('entropy', 0):.1f} бит\n"
            f"⚖️ Сложность: {report.get('score', 0):.1f}/100\n\n"
            f"⏳ Время взлома:\n"
            f"• Онлайн (Hydra HTTP): {estimate_crack_time(password, 'online')}\n"
            f"• Оффлайн (MD5): {estimate_crack_time(password, 'md5')}\n\n"
            f"📝 Рекомендации:\n{recommendations_text}"
        )

        msg = await message.answer(response, parse_mode=ParseMode.HTML)
        manager.track(msg)
        await state.update_data(manager=manager)
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        await message.answer("🔒 Введите пароль для проверки через главное меню")

@router.callback_query(F.data.startswith("check_password_"))
@message_cleaner
async def handle_existing_check(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        password = callback.data.split("check_password_", 1)[1]
        report, recommendations = calculate_password_strength(password)
        recommendations_text = "\n".join(f"• {rec}" for rec in recommendations)

        response = (
            f"🔍 <b>Анализ сгенерированного пароля:</b>\n<code>{password}</code>\n\n"
            f"{report}\n\n"
            f"📝 <b>Рекомендации:</b>\n{recommendations_text}"
        )

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        msg = await callback.message.answer(response, parse_mode=ParseMode.HTML, reply_markup=main_menu())
        data = await state.get_data()
        if manager := data.get('manager'):
            manager.track(msg)

        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("⚠️ Ошибка проверки", show_alert=True)

@router.callback_query(F.data == "check_hibp")
@message_cleaner
async def start_hibp_check(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer("🔒 Отправь пароль для проверки через HIBP...", show_alert=True)
        await callback.message.delete()

        await state.set_state(HIBPCheckStates.AWAITING_HIBP_PASSWORD)
        msg = await callback.message.answer(
            "✍️ <b>Введите пароль для проверки через HIBP:</b>\n"
            "▫️ Минимальная длина: 8 символов\n"
            "▫️ Проверяется утечка в базе Have I Been Pwned",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
                ]
            )
        )

        manager = MessageManager()
        manager.track(msg)
        await state.update_data(manager=manager)
    except Exception as e:
        logger.error(f"Ошибка инициализации проверки HIBP: {e}")
        await callback.answer("⚠️ Ошибка инициализации", show_alert=True)

@router.message(HIBPCheckStates.AWAITING_HIBP_PASSWORD)
@message_cleaner
async def process_hibp_check(message: Message, state: FSMContext):
    try:
        password = message.text.strip()
        if len(password) < 8:
            msg = await message.answer(
                "⚠️ Пароль должен быть минимум 8 символов!",
                reply_markup=main_menu()
            )
            manager = MessageManager()
            manager.track(msg)
            await state.update_data(manager=manager)
            await state.clear()
            return

        is_pwned, count = await check_hibp(password)
        response = (
            f"🔍 Проверка пароля через HIBP:\n<code>{password}</code>\n\n"
            f"{'⚠️ Пароль найден в утечках!' if is_pwned else '✅ Пароль не найден в утечках'}\n"
            f"Количество утечек: {count if is_pwned else 0}"
        )

        msg = await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=main_menu())
        manager = MessageManager()
        manager.track(msg)
        await state.update_data(manager=manager)
    except Exception as e:
        logger.error(f"Ошибка проверки HIBP: {e}")
        msg = await message.answer("⚠️ Ошибка при проверке HIBP", reply_markup=main_menu())
        manager = MessageManager()
        manager.track(msg)
        await state.update_data(manager=manager)
    finally:
        await state.clear()