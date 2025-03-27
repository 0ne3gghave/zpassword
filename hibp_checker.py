import hashlib
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def check_hibp(password: str) -> Optional[str]:
    """
    Проверяет пароль через Have I Been Pwned API с использованием k-анонимности.
    Возвращает количество утечек или None, если возникла ошибка.
    """
    try:
        # Хешируем пароль в SHA-1
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        # Запрос к HIBP API
        async with aiohttp.ClientSession() as session:
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"HIBP API вернул ошибку: {response.status}")
                    return None

                # Парсим ответ
                text = await response.text()
                for line in text.splitlines():
                    hash_suffix, count = line.split(':')
                    if hash_suffix == suffix:
                        return f"⚠️ Пароль найден в {count} утечках!"

                return "✅ Пароль не найден в известных утечках"

    except Exception as e:
        logger.error(f"Ошибка проверки HIBP: {e}")
        return None