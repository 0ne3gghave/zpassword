from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class User(BaseModel):
    """Модель пользователя для таблицы users"""
    user_id: int = Field(..., description="Уникальный идентификатор пользователя")
    username: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Имя пользователя в Telegram"
    )

class PasswordEntry(BaseModel):
    """Модель записи пароля для таблицы passwords"""
    id: int = Field(..., description="Уникальный ID записи")
    user_id: int = Field(..., description="ID владельца")
    password: str = Field(
        ...,
        min_length=8,
        max_length=15,
        description="Сгенерированный пароль"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Время создания записи"
    )

class Note(BaseModel):
    """Модель заметки для таблицы notes"""
    id: int = Field(..., description="Уникальный ID заметки")
    user_id: int = Field(..., description="ID владельца")
    password_id: int = Field(..., description="ID связанного пароля")
    content: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Содержание заметки"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Время создания заметки"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """Валидация содержания заметки"""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Содержание не может быть пустым!")
        return stripped