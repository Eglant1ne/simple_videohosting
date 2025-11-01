from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.user import User
from redis_client import redis_client

# Контекст для хеширования паролей с использованием bcrypt
pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие plain-пароля его хешу.
    
    :param plain_password: Пароль в открытом виде
    :type plain_password: str
    :param hashed_password: Хешированный пароль из базы данных
    :type hashed_password: str
    :return: True если пароль верный, иначе False
    :rtype: bool
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_hashed_password(password: str) -> str:
    """
    Генерирует bcrypt хеш для пароля.
    
    :param password: Пароль в открытом виде
    :type password: str
    :return: Хешированный пароль
    :rtype: str
    """
    return pwd_context.hash(password)


async def get_user_by_email(email: str, session: AsyncSession) -> User:
    """
    Находит пользователя по email адресу.
    
    :param email: Email адрес для поиска
    :type email: str
    :param session: Асинхронная сессия базы данных
    :type session: AsyncSession
    :return: Объект пользователя или None если не найден
    :rtype: User or None
    """
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().first()


async def get_user_by_username(username: str, session: AsyncSession) -> User:
    """
    Находит пользователя по имени пользователя.
    
    :param username: Имя пользователя для поиска
    :type username: str
    :param session: Асинхронная сессия базы данных
    :type session: AsyncSession
    :return: Объект пользователя или None если не найден
    :rtype: User or None
    """
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalars().first()


async def get_user_by_id(user_id: int, session: AsyncSession) -> User:
    """
    Находит пользователя по идентификатору.
    
    :param user_id: ID пользователя
    :type user_id: int
    :param session: Асинхронная сессия базы данных
    :type session: AsyncSession
    :return: Объект пользователя или None если не найден
    :rtype: User or None
    """
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalars().first()


def generate_blacklist_token_id(token_id: str) -> str:
    """
    Генерирует ключ для хранения токена в черном списке Redis.
    
    :param token_id: JWT ID (jti) токена
    :type token_id: str
    :return: Ключ для Redis в формате 'blacklisted_token:{jti}'
    :rtype: str
    """
    return f'blacklisted_token:{token_id}'


async def add_token_payload_to_blacklist(payload: dict) -> None:
    """
    Добавляет токен в черный список Redis.
    
    Токен сохраняется с временем жизни, соответствующим его expiration времени,
    чтобы автоматически удаляться из Redis после истечения срока действия.
    
    :param payload: Payload JWT токена
    :type payload: dict
    :return: None
    """
    if payload is not None:
        await redis_client.set(generate_blacklist_token_id(payload.get('jti')), value=1, exat=payload.get('exp', 0))


async def get_user_by_token_payload(payload: dict, session: AsyncSession) -> User:
    """
    Находит пользователя по payload JWT токена с проверкой валидности.
    
    Выполняет несколько проверок:
    1. Проверяет, не находится ли токен в черном списке
    2. Проверяет существование пользователя
    3. Проверяет соответствие версии токена
    
    :param payload: Payload JWT токена
    :type payload: dict
    :param session: Асинхронная сессия базы данных
    :type session: AsyncSession
    :return: Объект пользователя или None если токен невалиден
    :rtype: User or None
    
    :raises Exception: При ошибках обработки payload или доступа к базе данных
    """
    try:
        # Проверка черного списка
        if await redis_client.exists(generate_blacklist_token_id(payload.get('jti'))):
            return None

        # Получение пользователя и проверка версии токена
        user: User = await get_user_by_id(int(payload['sub']), session)
        if user is None or user.token_version != int(payload['version']):
            return None

        return user

    except Exception:
        return None
