from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from database.user import User
from sqlalchemy.future import select
from database.session import async_session
from .schemas import UserCreate, UserLogin
from fastapi.responses import ORJSONResponse
from .utils import verify_password, generate_hashed_password
from jwt_tokens.token_generator import create_access_token, create_access_token_payload, \
    create_refresh_token_payload, create_refresh_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(prefix='/auth', tags=['Auth'])


async def email_exist(email: str, session) -> bool:
    result = await session.execute(
        select(User.email).where(User.email == email)
    )
    return result.scalar_one_or_none() is not None


async def username_exist(username: str, session) -> bool:
    result = await session.execute(
        select(User.username).where(User.username == username)
    )
    return result.scalar_one_or_none() is not None


async def create_user(user: UserCreate, session: AsyncSession):
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
async def register_user(user: UserCreate):
    async with async_session() as session:
        try:
            if await email_exist(user.email, session):
                return ORJSONResponse(
                    {"msg": "Почта уже зарегистрирована."},
                    status_code=400,
                )
            if await username_exist(user.username, session):
                return ORJSONResponse(
                    {"msg": "Аккаунт с таким именем уже существует."},
                    status_code=400,
                )

            await create_user(user, session)
            return ORJSONResponse(
                {"msg": "Успешно."},
                status_code=200
            )

        except Exception as e:
            await session.rollback()
            return ORJSONResponse({"msg": "Ошибка регистрации!"},
                                  status_code=500,
                                  )


async def get_user_by_login(user: UserLogin, password: str, session: AsyncSession):
    if "@" in user.login:
        user_login = await email_exist(user.login, session)
    else:
        user_login = await username_exist(user.login, session)

    if not user_login or verify_password(plain_password=password, hashed_password=user.password_hash) is False:
        return None
    return user_login


@router.post("/login/")
async def auth_user(user: UserLogin):
    async with async_session() as session:
        try:
            authenticated_user = await get_user_by_login(
                user,
                user.password,
                session
            )

            if not authenticated_user:
                return ORJSONResponse(
                    {"msg": "Неверная почта/имя пользователя или пароль."},
                    status_code=401
                )

            access_token = create_access_token(create_access_token_payload(authenticated_user))
            refresh_token = create_refresh_token(create_refresh_token_payload(authenticated_user))

            return ORJSONResponse(
                {"msg": "Ошибка аутентификации.", "access_token": access_token},
                status_code=200
            )
        except Exception as e:
            return ORJSONResponse(
                {"msg": "Ошибка аутентификации."},
                status_code=500
            )
