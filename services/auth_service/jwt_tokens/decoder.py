import jwt

from config import RSA_KEYS
from jwt_tokens.token_generator import ALGORITHM


def decode_token_payload(token: str) -> dict:
    """
    Декодирует и верифицирует JWT токен.

    Использует RSA публичный ключ для проверки подписи токена
    и возвращает payload в случае успешной верификации.

    :param token: JWT токен в строковом формате
    :type token: str
    :return: Payload токена в виде словаря или None при ошибке верификации
    :rtype: dict or None

    :raises Exception: При критических ошибках декодирования (перехватывается и возвращается None)
    """
    try:
        return jwt.decode(token, RSA_KEYS.public_key, algorithms=[ALGORITHM])
    except Exception:
        return None
