from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import async_session
from database.user import User

from .router import router
from .schemas import UserCreate
from .utils import get_user_by_email, get_user_by_username, generate_hashed_password


async def create_user(user: UserCreate, session: AsyncSession) -> User:
    hashed_password = generate_hashed_password(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=hashed_password
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@router.post("/register/")
async def register_user(user: UserCreate) -> ORJSONResponse:
    async with async_session() as session:
        try:
            if await get_user_by_email(user.email, session):
                return ORJSONResponse(
                    {"msg": "Почта уже зарегистрирована."},
                    status_code=400,
                )
            if await get_user_by_username(user.username, session):
                return ORJSONResponse(
                    {"msg": "Аккаунт с таким именем уже существует."},
                    status_code=400,
                )

            await create_user(user, session)
            return ORJSONResponse(
                {"msg": "Успешно."},
                status_code=200
            )

        except Exception:
            await session.rollback()
            return ORJSONResponse({"msg": "Ошибка регистрации!"},
                                  status_code=500,
                                  )
