import math
from typing import Tuple, Dict, List
import hashlib
import aiohttp

class AdvancedPasswordAnalyzer:
    """Модернизированный анализатор с учетом современных реалий атак"""

    HYDRA_SPEED: Dict[str, float] = {
        'ssh': 1200,
        'http_form': 4500,
        'rdp': 800
    }

    GPU_HASH_SPEED: Dict[str, float] = {
        'MD5': 25.6e6,
        'SHA-256': 2.1e6,
        'bcrypt': 12e3,
        'NTLM': 45e6
    }

    COMPLEXITY_FACTORS = {
        'length': 4.0,
        'lower': 1.0,
        'upper': 1.2,
        'digit': 1.3,
        'special': 1.5
    }

    def __init__(self, password: str):
        self.password = password
        self.entropy = self._calculate_entropy()
        self.complexity_score = self._calculate_complexity()

    def _calculate_entropy(self) -> float:
        char_sets = {
            'lower': 26,
            'upper': 26,
            'digit': 10,
            'special': 33
        }

        active_sets = [
            any(c.islower() for c in self.password),
            any(c.isupper() for c in self.password),
            any(c.isdigit() for c in self.password),
            any(not c.isalnum() for c in self.password)
        ]

        charset_size = sum(
            size
            for size, used
            in zip(char_sets.values(), active_sets)
            if used
        )

        charset_size = charset_size or 1
        return len(self.password) * math.log2(charset_size)

    def _calculate_complexity(self) -> float:
        score = 1.0
        score += len(self.password) * self.COMPLEXITY_FACTORS['length']
        score += 2 * sum([
            self.COMPLEXITY_FACTORS['lower'] * any(c.islower() for c in self.password),
            self.COMPLEXITY_FACTORS['upper'] * any(c.isupper() for c in self.password),
            self.COMPLEXITY_FACTORS['digit'] * any(c.isdigit() for c in self.password),
            self.COMPLEXITY_FACTORS['special'] * any(not c.isalnum() for c in self.password)
        ])
        return min(score, 100)

    def calculate_crack_time(self, attack_type: str, hash_alg: str = 'MD5') -> Dict[str, str]:
        combinations = 2 ** self.entropy

        if attack_type == 'online':
            protocol = 'http_form'
            speed = self.HYDRA_SPEED[protocol] / 60
            time_seconds = combinations / speed
            return {'hydra': self._format_time(time_seconds)}

        elif attack_type == 'offline':
            speed = self.GPU_HASH_SPEED.get(hash_alg, 1e6)
            time_seconds = combinations / speed
            return {
                'gpu_cluster': self._format_time(time_seconds),
                'hash_alg': hash_alg.upper()
            }

        return {}

    @staticmethod
    def _format_time(seconds: float) -> str:
        if seconds < 1:
            return "мгновенно"

        units = [
            ('веков', 3.154e7),
            ('лет', 3.154e7),
            ('месяцев', 2.628e6),
            ('дней', 86400),
            ('часов', 3600),
            ('минут', 60),
            ('секунд', 1)
        ]

        result = []
        for unit, divisor in units:
            if seconds >= divisor:
                value = int(seconds // divisor)
                seconds %= divisor
                result.append(f"{value} {unit}")
                if len(result) == 2: break

        return " ".join(result) or "<1 сек"

    def generate_report(self) -> Tuple[str, List[str]]:
        hydra_time = self.calculate_crack_time('online')['hydra']
        md5_time = self.calculate_crack_time('offline', 'MD5')['gpu_cluster']
        bcrypt_time = self.calculate_crack_time('offline', 'bcrypt')['gpu_cluster']

        report = (
            f"🔐 Анализ пароля: '{self.password}'\n"
            f"📈 Энтропия: {self.entropy:.1f} бит\n"
            f"⚖️ Сложность: {self.complexity_score:.1f}/100\n\n"
            f"⏳ Время взлома:\n"
            f"• Онлайн (Hydra HTTP): {hydra_time}\n"
            f"• Оффлайн (MD5): {md5_time}\n"
            f"• Оффлайн (bcrypt): {bcrypt_time}"
        )

        recommendations = []
        if self.complexity_score < 60:
            recommendations.append("Используйте 4+ категорий символов")
        if len(self.password) < 12:
            recommendations.append("Увеличьте длину до 16+ символов")
        if not any(not c.isalnum() for c in self.password):
            recommendations.append("Добавьте спецсимволы")
        if self.entropy < 60:
            recommendations.append("Увеличьте общую энтропию пароля")
        if len(self.password) < 8:
            recommendations.append("Используйте минимум 12 символов")
        return report, recommendations

async def check_hibp(password: str) -> Tuple[bool, int]:
    """Проверка пароля через HIBP API"""
    sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]

    async with aiohttp.ClientSession() as session:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        async with session.get(url) as response:
            if response.status != 200:
                return False, 0
            text = await response.text()
            for line in text.splitlines():
                hash_suffix, count = line.split(':')
                if hash_suffix == suffix:
                    return True, int(count)
            return False, 0

def calculate_password_strength(password: str) -> tuple[dict, list]:
    entropy = len(password) * 4
    score = min(100, entropy * 5)

    recommendations = []
    if len(password) < 12:
        recommendations.append("Используйте пароли длиной от 12 символов")

    return (
        {"entropy": entropy, "score": score},
        recommendations
    )