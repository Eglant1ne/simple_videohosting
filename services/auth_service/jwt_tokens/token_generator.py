import jwt
import datetime

from config import RSA_KEYS

# Константы для времени жизни токенов
ACCESS_TOKEN_EXPIRE_MINUTES = 30
"""Время жизни access токена в минутах (30 минут)."""

REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 2 * 24
"""Время жизни refresh токена в минутах (2 дня)."""

ALGORITHM = "RS256"
"""Алгоритм шифрования JWT токенов (RSA Signature with SHA-256)."""


def create_access_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    """
    Создает JWT access токен с указанным payload.

    Access токен используется для аутентификации пользователя при доступе
    к защищенным ресурсам API. Имеет короткое время жизни.

    :param data: Payload токена (должен содержать claims пользователя)
    :type data: dict
    :param expires_delta: Кастомное время жизни токена, если не указано - используется стандартное
    :type expires_delta: datetime.timedelta or None
    :return: Закодированный JWT access токен
    :rtype: str
    """
    to_encode: dict = data.copy()
    now: datetime.datetime = datetime.datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "nbf": now, "iat": now})
    token = jwt.encode(to_encode, RSA_KEYS.private_key, algorithm=ALGORITHM)
    return token


def create_refresh_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    """
    Создает JWT refresh токен с указанным payload.

    Refresh токен используется для получения новой пары access/refresh токенов
    без необходимости повторной аутентификации пользователя. Имеет длительное время жизни.

    :param data: Payload токена (должен содержать claims пользователя)
    :type data: dict
    :param expires_delta: Кастомное время жизни токена, если не указано - используется стандартное
    :type expires_delta: datetime.timedelta or None
    :return: Закодированный JWT refresh токен
    :rtype: str
    """
    to_encode: dict = data.copy()
    now: datetime.datetime = datetime.datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "nbf": now, "iat": now})
    token: str = jwt.encode(to_encode, RSA_KEYS.private_key, algorithm=ALGORITHM)
    return token