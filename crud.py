import logging
import os
import asyncpg
from typing import List, Optional, cast

from database import get_connection
from models import PasswordEntry, Note, User

logger = logging.getLogger(__name__)

async def get_user(user_id: int) -> Optional[User]:
    """Получение информации о пользователе"""
    try:
        async with get_connection() as conn:
            record = await conn.fetchrow(
                "SELECT user_id, username FROM users WHERE user_id = $1",
                user_id
            )
            return User(**dict(record)) if record else None
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка БД: {e}", exc_info=True)
        raise

async def register_user(user_id: int, username: Optional[str]) -> None:
    """Регистрация/обновление пользователя"""
    try:
        async with get_connection() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE 
                SET username = EXCLUDED.username""",
                user_id, username or ""
            )
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка регистрации: {e}", exc_info=True)
        raise

async def save_password(user_id: int, password: str) -> int:
    """Сохранение пароля с лимитом 1000 записей. Возвращает ID пароля."""
    try:
        async with get_connection() as conn:
            async with conn.transaction():
                await conn.execute("""
                    WITH to_delete AS (
                        SELECT ctid FROM passwords
                        WHERE user_id = $1
                        ORDER BY id ASC
                        LIMIT GREATEST((SELECT COUNT(*) FROM passwords WHERE user_id = $1) - 999, 0)
                    )
                    DELETE FROM passwords WHERE ctid IN (SELECT ctid FROM to_delete)
                """, user_id)

                record = await conn.fetchrow(
                    "INSERT INTO passwords (user_id, password) VALUES ($1, $2) RETURNING id",
                    user_id, password
                )
                return cast(int, record['id'])
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка сохранения: {e}", exc_info=True)
        raise

async def get_passwords(user_id: int, page: int = 1, per_page: int = 15) -> List[PasswordEntry]:
    """Получение паролей с пагинацией"""
    try:
        async with get_connection() as conn:
            records = await conn.fetch(
                """SELECT id, user_id, password, created_at
                FROM passwords
                WHERE user_id = $1
                ORDER BY id DESC
                LIMIT $2 OFFSET $3""",
                user_id, per_page, (page - 1) * per_page
            )
            return [PasswordEntry(**dict(record)) for record in records]
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка запроса: {e}", exc_info=True)
        raise

async def get_password_count(user_id: int) -> int:
    """Количество сохраненных паролей"""
    try:
        async with get_connection() as conn:
            return cast(int, await conn.fetchval(
                "SELECT COUNT(*) FROM passwords WHERE user_id = $1",
                user_id
            ))
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка подсчета: {e}", exc_info=True)
        raise

async def add_note(user_id: int, password_id: int, content: str) -> Note:
    """Создание заметки привязанной к паролю"""
    try:
        async with get_connection() as conn:
            record = await conn.fetchrow(
                """INSERT INTO notes (user_id, password_id, content)
                VALUES ($1, $2, $3)
                RETURNING id, user_id, password_id, content, created_at""",
                user_id, password_id, content[:255]
            )
            return Note(**dict(record))
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка создания: {e}", exc_info=True)
        raise

async def get_notes(user_id: int, page: int = 1, per_page: int = 8) -> List[Note]:
    """Получение всех заметок пользователя с пагинацией"""
    try:
        async with get_connection() as conn:
            records = await conn.fetch(
                """SELECT id, user_id, password_id, content, created_at
                FROM notes
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3""",
                user_id, per_page, (page - 1) * per_page
            )
            return [Note(**dict(record)) for record in records]
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка выборки: {e}", exc_info=True)
        raise

async def get_note_by_id(note_id: int) -> Optional[Note]:
    """Получение заметки по ID"""
    try:
        async with get_connection() as conn:
            record = await conn.fetchrow(
                "SELECT id, user_id, password_id, content, created_at FROM notes WHERE id = $1",
                note_id
            )
            return Note(**dict(record)) if record else None
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка поиска: {e}", exc_info=True)
        raise

async def delete_note(note_id: int) -> bool:
    """Удаление заметки"""
    try:
        async with get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM notes WHERE id = $1 RETURNING id",
                note_id
            )
            return "DELETE 1" in result
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка удаления: {e}", exc_info=True)
        return False

async def delete_password(password_id: int) -> bool:
    try:
        async with get_connection() as conn:
            result = await conn.execute(
                "DELETE FROM passwords WHERE id = $1 RETURNING id",
                password_id
            )
            return "DELETE 1" in result
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка удаления: {e}", exc_info=True)
        return False

async def export_note(note_id: int) -> str:
    """Экспорт заметки в файл"""
    filename = None
    try:
        note = await get_note_by_id(note_id)
        if not note:
            raise ValueError("Заметка не найдена")

        filename = f"note_{note_id}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"ID: {note.id}\n")
            f.write(f"Password ID: {note.password_id}\n")
            f.write(f"Содержание:\n{note.content}")

        return filename
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}", exc_info=True)
        raise
    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                logger.error(f"Ошибка очистки: {e}", exc_info=True)

async def clear_all_data(user_id: int) -> None:
    """Полная очистка данных пользователя"""
    try:
        async with get_connection() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM passwords WHERE user_id = $1", user_id)
                await conn.execute("DELETE FROM notes WHERE user_id = $1", user_id)
                logger.info(f"Данные пользователя {user_id} очищены")
    except asyncpg.PostgresError as e:
        logger.error(f"Ошибка очистки: {e}", exc_info=True)
        raise

async def get_last_password_id(user_id: int) -> Optional[int]:
    """Получение ID последнего пароля пользователя"""
    try:
        async with get_connection() as conn:
            record = await conn.fetchrow(
                "SELECT id FROM passwords WHERE user_id = $1 ORDER BY id DESC LIMIT 1",
                user_id
            )
            return record['id'] if record else None
    except Exception as e:
        logger.error(f"Ошибка получения пароля: {e}")
        return None
