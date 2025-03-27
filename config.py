import os
from dotenv import load_dotenv
from typing import Optional
from urllib.parse import quote_plus


class ConfigError(Exception):
    pass


# Явное указание пути к .env в корне проекта
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(ENV_PATH, encoding='utf-8')


def get_env(var: str, default: Optional[str] = None) -> str:
    """Безопасное получение переменных окружения с валидацией"""
    value = os.getenv(var, default)
    if value is None:
        raise ConfigError(f"Отсутствует обязательная переменная: {var}")
    return value


try:
    # Основные настройки
    TOKEN: str = get_env("BOT_TOKEN")

    # Настройки PostgreSQL с экранированием спецсимволов
    PG_HOST: str = get_env("PG_HOST", "192.168.10.99")
    PG_PORT: int = int(get_env("PG_PORT", "5432"))
    PG_USER: str = get_env("PG_USER", "bot_user")
    PG_PASSWORD: str = quote_plus(get_env("PG_PASSWORD", "bot_password"))  # Экранирование
    PG_DB: str = get_env("PG_DB", "bot_db")

    # Формирование DSN с учетом экранирования
    DATABASE_URL: str = (
        f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    )

except Exception as e:
    raise ConfigError(f"Ошибка конфигурации: {str(e)}") from e