from __future__ import annotations
import asyncpg
from config import DATABASE_URL
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

from typing import Optional
_pool: Optional[asyncpg.Pool] = None


async def create_pool() -> None:
    """Инициализация пула соединений с PostgreSQL."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ Пул соединений PostgreSQL инициализирован")
        except Exception as e:
            logger.critical(f"❌ Ошибка создания пула: {e}", exc_info=True)
            raise


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Контекстный менеджер для безопасного использования соединений."""
    global _pool

    if _pool is None:
        await create_pool()

    conn = await _pool.acquire()
    try:
        yield conn
    finally:
        await _pool.release(conn)


async def init_db() -> None:
    """Инициализация структуры БД с транзакцией."""
    async with get_connection() as conn:
        try:
            async with conn.transaction():
                await conn.execute("""
                    DROP TABLE IF EXISTS 
                        notes, 
                        passwords, 
                        users CASCADE
                """)

                await conn.execute("""
                    CREATE TABLE users (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(32)
                    )
                """)

                await conn.execute("""
                    CREATE TABLE passwords (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(user_id) 
                            ON DELETE CASCADE,
                        password VARCHAR(15) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                await conn.execute("""
                    CREATE TABLE notes (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(user_id) 
                            ON DELETE CASCADE,
                        password_id INT REFERENCES passwords(id) 
                            ON DELETE CASCADE,
                        content VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                await conn.execute("""
                    CREATE INDEX idx_passwords_user 
                    ON passwords(user_id, created_at DESC)
                """)

                logger.info("🚀 База данных инициализирована")

        except asyncpg.PostgresError as e:
            logger.error(f"🔥 Ошибка SQL: {e}", exc_info=True)
            raise
