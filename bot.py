import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TOKEN
from database import create_pool, init_db
from commands import router as commands_router
from callbacks import router as callbacks_router
from password_check import router as password_check_router
from keyboards import main_menu
from decorators import message_cleaner, MessageManager
from hibp_checker import check_hibp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

hibp_router = Router()


class HIBPCheckStates(StatesGroup):
    AWAITING_HIBP_PASSWORD = State()


@hibp_router.callback_query(F.data == "check_hibp")
@message_cleaner
async def start_hibp_check(callback: CallbackQuery, state: FSMContext):
    """Инициирует проверку пароля через HIBP"""
    try:
        await callback.answer("🔒 Отправь пароль для проверки через HIBP...", show_alert=True)

        await callback.message.delete()

        await state.set_state(HIBPCheckStates.AWAITING_HIBP_PASSWORD)

        msg = await callback.message.answer(
            "✍️ <b>Введите пароль для проверки через HIBP:</b>\n"
            "▫️ Минимальная длина: 8 символов\n"
            "▫️ Проверка через Have I Been Pwned",
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
        logger.error(f"Ошибка инициализации HIBP проверки: {e}")
        await callback.answer("⚠️ Ошибка инициализации", show_alert=True)


@hibp_router.message(HIBPCheckStates.AWAITING_HIBP_PASSWORD)
@message_cleaner
async def process_hibp_check(message: Message, state: FSMContext):
    """Обрабатывает введенный пароль и проверяет через HIBP"""
    try:
        password = message.text.strip()

        if len(password) < 8:
            await message.answer(
                "⚠️ Пароль должен быть минимум 8 символов!",
                reply_markup=main_menu()
            )
            await state.clear()
            return

        result = await check_hibp(password)

        response = (
            f"🔍 Проверка пароля через HIBP:\n<code>{password}</code>\n\n"
            f"{result if result else '⚠️ Ошибка проверки через HIBP'}"
        )

        await message.answer(
            response,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu()
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка обработки HIBP: {e}")
        await message.answer(
            "⚠️ Произошла ошибка при проверке",
            reply_markup=main_menu()
        )
        await state.clear()


async def main() -> None:
    """Основная функция инициализации бота"""
    global bot
    try:
        await create_pool()
        logger.info("✅ PostgreSQL connection pool initialized")

        bot = Bot(
            token=TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        dp = Dispatcher()

        dp.include_router(commands_router)
        dp.include_router(password_check_router)
        dp.include_router(callbacks_router)
        dp.include_router(hibp_router)

        await init_db()
        logger.info("✅ Database schema initialized")

        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🚀 Bot started in polling mode...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.critical(f"🔥 Critical error: {e}", exc_info=True)
    finally:
        from database import _pool
        if _pool:
            await _pool.close()
            logger.info("🗄 Connection pool closed")
        if 'bot' in locals():
            await bot.close()
            logger.info("🤖 Bot shutdown completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Bot stopped by user")
