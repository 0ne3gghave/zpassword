from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Сгенерировать", callback_data="generate")],
            [InlineKeyboardButton(text="📋 Список паролей", callback_data="pswd_list")],
            [InlineKeyboardButton(text="🛡 Проверить свой пароль", callback_data="check_custom")],
            [InlineKeyboardButton(text="🌐 Проверить надежность Online", callback_data="check_hibp")],  # Новая кнопка
            [
                InlineKeyboardButton(text="🌐 GitHub", url="https://github.com/0ne3gghave/zpassword"),
                InlineKeyboardButton(text="🔒 Практики безопасности", url="https://habr.com/ru/articles/841896/")
            ]
        ]
    )

def password_length_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="8", callback_data="length_8")],
            [InlineKeyboardButton(text="10", callback_data="length_10")],
            [InlineKeyboardButton(text="12", callback_data="length_12")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ]
    )

def passwords_pagination(page: int, total_pages: int, passwords: List[object],
                         per_page: int = 15) -> InlineKeyboardMarkup:
    page = max(1, min(page, total_pages))
    keyboard = []

    for pswd in passwords[:per_page]:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🔑 {pswd.password}",
                callback_data=f"copy_{pswd.password}"
            ),
            InlineKeyboardButton(
                text="🗑️ Удалить",
                callback_data=f"delete_{pswd.id}"
            )
        ])

    pagination_row = []
    if page > 1:
        pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"pswd_page_{page - 1}"))
    pagination_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current"))
    if page < total_pages:
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"pswd_page_{page + 1}"))

    keyboard.append(pagination_row)
    keyboard.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def after_generation_keyboard(password: str, length: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Генерировать еще",
                    callback_data=f"regenerate_{length}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )