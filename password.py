import random
import string
from typing import Literal

ALLOWED_LENGTHS = Literal['8', '10', '12']
SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~"


def generate_password(length: ALLOWED_LENGTHS) -> str:
    """
    Генерирует безопасный пароль заданной длины (8/10/12 символов)
    с гарантированным наличием всех категорий символов.

    Соответствует требованиям системы:
    - Фиксированные длины из интерфейса (keyboards.py)
    - Ограничение модели данных (models.PasswordEntry)
    - PostgreSQL schema (passwords.password VARCHAR(15))

    Пример использования:
    generate_password('12') → "aD4#kL9!zX@1"
    """
    length_int = int(length)

    categories = {
        'lowercase': string.ascii_lowercase,
        'uppercase': string.ascii_uppercase,
        'digits': string.digits,
        'symbols': SYMBOLS
    }

    required = [random.choice(chars) for chars in categories.values()]

    remaining_chars = [
        random.choice(''.join(categories.values()))
        for _ in range(length_int - len(required))
    ]

    password_chars = required + remaining_chars
    random.shuffle(password_chars)

    return ''.join(password_chars)

def estimate_crack_time(password: str, mode: str = 'md5') -> str:
    """Оценка времени взлома с учетом режима атаки"""
    if not password:
        return "Невозможно оценить"

    charsets = {
        "lower": 26,  # a-z
        "upper": 26,  # A-Z
        "digits": 10,  # 0-9
        "special": 33  # !@#$%^&*() и т.д.
    }

    used_charsets = {
        "lower": any(c.islower() for c in password),
        "upper": any(c.isupper() for c in password),
        "digits": any(c.isdigit() for c in password),
        "special": any(not c.isalnum() for c in password)
    }

    charset_size = sum(
        size for name, size in charsets.items()
        if used_charsets[name]
    )

    if charset_size == 0:
        return "Недопустимые символы"

    length = len(password)
    combinations = charset_size ** length

    speeds = {
        'online': 15,       # 15 попыток/сек
        'md5': 1_000_000,   # 1 млн попыток/сек
        'bcrypt': 100       # 100 попыток/сек
    }

    speed = speeds.get(mode, 1_000_000)
    seconds = combinations / speed

    minutes = int(seconds // 60)
    if minutes < 1:
        return "< 1 минуты"
    elif minutes < 60:
        return f"~{minutes} минут"
    elif minutes < 1440:
        return f"~{minutes // 60} часов"
    else:
        return f"~{minutes // 1440} дней"

