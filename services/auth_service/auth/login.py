from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import ORJSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from database.user import User
from database.session import async_session

from jwt_tokens.token_generator import create_access_token, create_access_token_payload, \
    create_refresh_token_payload, create_refresh_token
from .router import router

from .schemas import UserLogin
from .utils import verify_password, get_user_by_email, get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token/")


async def authorization_by_login(user_login: UserLogin, session: AsyncSession) -> User:
    if "@" in user_login.login:
        user: User = await get_user_by_email(user_login.login, session)
    else:
        user: User = await get_user_by_username(user_login.login, session)
    verify_pass = verify_password(user_login.password, user.password_hash)
    if user is None or not verify_pass:
        return None

    return user


@router.post("/login/")
async def authorization_user(user_login: UserLogin) -> ORJSONResponse:
    async with async_session() as session:
        try:
            authenticated_user = await authorization_by_login(
                user_login,
                session
            )

            if not authenticated_user:
                return ORJSONResponse(
                    {"msg": "Неверная почта/имя пользователя или пароль."},
                    status_code=401
                )

            access_token: str = create_access_token(
                create_access_token_payload(authenticated_user)
            )
            refresh_token: str = create_refresh_token(
                create_refresh_token_payload(authenticated_user)
            )

            response = ORJSONResponse(
                {"msg": "Успешная авторизация."},
                status_code=200
            ) 
            response.set_cookie(
                'access_token',
                access_token,
                secure=True,
                httponly=True,
                samesite='strict',
            )
            response.set_cookie(
                'refresh_token',
                refresh_token,
                secure=True,
                httponly=True,
                samesite='strict',
            )
            return response

        except Exception as e:
            return ORJSONResponse(
                {"msg": f"Ошибка авторизации. {e}"},
                status_code=500
            )
