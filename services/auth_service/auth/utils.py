from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.user import User
from redis_client import redis_client

pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_hashed_password(password: str) -> str:
    return pwd_context.hash(password)


async def get_user_by_email(email: str, session: AsyncSession) -> User:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().first()


async def get_user_by_username(username: str, session: AsyncSession) -> User:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalars().first()


async def get_user_by_id(user_id: int, session: AsyncSession) -> User:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalars().first()


def generate_blacklist_token_id(token_id: str) -> None:
    return f'blacklisted_token:{token_id}'


async def add_token_payload_to_blacklist(payload: dict) -> None:
    if payload is not None:
        await redis_client.set(generate_blacklist_token_id(payload.get('jti')), value=1, exat=payload.get('exp', 0))


async def get_user_by_token_payload(payload: dict, session: AsyncSession) -> User:
    try:
        if await redis_client.exists(generate_blacklist_token_id(payload.get('jti'))):
            return None

        user: User = await get_user_by_id(int(payload['sub']), session)
        if user is None or user.token_version != int(payload['version']):
            return None

        return user

    except Exception:
        return None
