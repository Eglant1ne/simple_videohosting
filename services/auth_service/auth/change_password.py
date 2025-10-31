from fastapi import Cookie
from fastapi.responses import ORJSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from database.user import User
from database.session import async_session

from jwt_tokens.decoder import decode_token_payload
from jwt_tokens.utils import token_payload_is_access

from .router import router
from .utils import generate_hashed_password, verify_password, get_user_by_token_payload
from .schemas import ChangePassword


async def change_password_db(user: User, new_password: str, session: AsyncSession) -> None:
    await session.execute(
        update(User).where(User.id == user.id).values(password_hash=generate_hashed_password(new_password),
                                                      token_version=User.token_version + 1)
    )
    await session.commit()


@router.post('/change_password/')
async def change_password(password_change: ChangePassword, access_token: str = Cookie(None)) -> ORJSONResponse:
    try:
        payload: dict = decode_token_payload(access_token)
        if not token_payload_is_access(payload):
            raise ValueError('Это не access token')

        async with async_session() as session:
            user: User = await get_user_by_token_payload(payload, session)

        if user is None:
            raise ValueError('Пользователь не существует')

    except Exception as e:
        return ORJSONResponse(
            {'msg': f'Не удалось авторизоваться по предоставленным данным'},
            status_code=401)

    if not verify_password(plain_password=password_change.old_password, hashed_password=user.password_hash):
        return ORJSONResponse(
            {'msg': 'Неправильный старый пароль'},
            status_code=400
        )
    async with async_session() as session:
        await change_password_db(user=user, new_password=password_change.new_password,
                                 session=session)

    response = ORJSONResponse(
        {'msg': 'Пароль успешно изменён'},
        status_code=200
    )
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    return response
