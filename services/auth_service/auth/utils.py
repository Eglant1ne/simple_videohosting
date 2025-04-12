from passlib.context import CryptContext
from sqlalchemy import select

from database.user import User

pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_hashed_password(password) -> str:
    return pwd_context.hash(password)


async def get_user_by_email(email: str, session) -> User:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().first()


async def get_user_by_username(username: str, session) -> User:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalars().first()
