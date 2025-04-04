import logging
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from decorators import message_cleaner, MessageManager
from keyboards import main_menu
from password import estimate_crack_time
from security import calculate_password_strength
import hashlib
import aiohttp

router = Router()
logger = logging.getLogger(__name__)

class PasswordCheckStates(StatesGroup):
    AWAITING_CUSTOM_PASSWORD = State()
    AWAITING_HIBP_PASSWORD = State()

@router.callback_query(F.data == "check_custom")
@message_cleaner
async def start_custom_check(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer("🔒 Отправь свой пароль в следующем сообщении...", show_alert=True)
        await callback.message.delete()
        await state.set_state(PasswordCheckStates.AWAITING_CUSTOM_PASSWORD)
        msg = await callback.message.answer(
            "✍️ <b>Введите пароль для проверки:</b>\n"
            "▫️ Минимальная длина: 8 символов\n"
            "▫️ Можно использовать: A-Z, a-z, 0-9, специальные символы",
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
        logger.error(f"Ошибка инициализации проверки: {e}")
        await callback.answer("⚠️ Ошибка инициализации проверки", show_alert=True)

@router.message(PasswordCheckStates.AWAITING_CUSTOM_PASSWORD)
@message_cleaner
async def process_custom_check(message: Message, state: FSMContext):
    try:
        password = message.text.strip()
        if len(password) < 8:
            await message.answer(
                "⚠️ Пароль должен содержать минимум 8 символов",
                reply_markup=main_menu()
            )
            await state.clear()
            return

        report, recommendations = calculate_password_strength(password)
        recommendations_text = "\n".join(
            f"• {rec}" for rec in recommendations) if recommendations else "✅ Пароль соответствует базовым требованиям"

        online_time = estimate_crack_time(password, mode='online')
        offline_md5_time = estimate_crack_time(password, mode='md5')

        response = (
            f"🔍 <b>Анализ надежности пароля:</b>\n<code>{password}</code>\n\n"
            f"📈 Энтропия: {report['entropy']:.1f} бит\n"
            f"⚖️ Сложность: {report['score']:.1f}/100\n\n"
            f"⏳ <b>Время взлома при компрометации:</b>\n"
            f"• Онлайн (Hydra HTTP): {online_time}\n"
            f"• Оффлайн (MD5): {offline_md5_time}\n\n"
            f"📝 <b>Рекомендации:</b>\n{recommendations_text}"
        )

        await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка проверки пароля: {e}")
        await message.answer("⚠️ Произошла ошибка при анализе пароля", reply_markup=main_menu())
        await state.clear()

@router.callback_query(F.data == "check_hibp")
@message_cleaner
async def start_hibp_check(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer("🔒 Отправь пароль для проверки через HIBP...", show_alert=True)
        await callback.message.delete()
        await state.set_state(PasswordCheckStates.AWAITING_HIBP_PASSWORD)
        msg = await callback.message.answer(
            "✍️ <b>Введите пароль для проверки в HIBP:</b>\n"
            "▫️ Пароль будет проверен безопасно через SHA-1 хеш\n"
            "▫️ Минимальная длина: 8 символов",
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
        await callback.answer("⚠️ Ошибка инициализации проверки", show_alert=True)

@router.message(PasswordCheckStates.AWAITING_HIBP_PASSWORD)
@message_cleaner
async def process_hibp_check(message: Message, state: FSMContext):
    try:
        password = message.text.strip()
        if len(password) < 8:
            await message.answer(
                "⚠️ Пароль должен содержать минимум 8 символов",
                reply_markup=main_menu()
            )
            await state.clear()
            return

        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.pwnedpasswords.com/range/{prefix}") as response:
                if response.status != 200:
                    raise Exception(f"HIBP API вернул ошибку: {response.status}")
                hashes = await response.text()

        found = False
        count = 0
        for line in hashes.splitlines():
            if not line.strip():
                continue
            try:
                hash_suffix, occurrences = line.split(':', 1)
                if hash_suffix.strip() == suffix:
                    found = True
                    count = int(occurrences.strip())
                    break
            except ValueError as e:
                logger.warning(f"Некорректная строка в ответе HIBP: {line} - {e}")
                continue

        if found:
            response = (
                f"🔍 Проверка пароля в HIBP:\n<code>{password}</code>\n\n"
                f"⚠️ Этот пароль был скомпрометирован!\n"
                f"📊 Обнаружен {count} раз(а) в утечках\n"
                f"Рекомендуем сменить пароль немедленно!"
            )
        else:
            response = (
                f"🔍 Проверка пароля в HIBP:\n<code>{password}</code>\n\n"
                f"✅ Пароль не найден в известных утечках"
            )

        await message.answer(response, parse_mode=ParseMode.HTML, reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка проверки HIBP: {e}")
        await message.answer(
            "⚠️ Ошибка при проверке через HIBP",
            reply_markup=main_menu()
        )
        await state.clear()
