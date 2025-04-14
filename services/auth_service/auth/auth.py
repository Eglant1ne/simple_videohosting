import asyncio

from fastapi import Cookie
from fastapi.responses import ORJSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from database.user import User
from database.session import async_session

from jwt_tokens.token_generator import create_access_token, create_refresh_token
from jwt_tokens.payload_generator import create_access_token_payload, create_refresh_token_payload
from jwt_tokens.decoder import decode_token_payload
from jwt_tokens.utils import token_payload_is_access, token_payload_is_refresh

from redis_client import redis_client

from .router import router

from .schemas import UserLogin, TokenBody
from .utils import verify_password, get_user_by_email, get_user_by_username, get_user_by_token_payload, \
    add_token_payload_to_blacklist, generate_blacklist_token_id


async def authorization_by_login(user_login: UserLogin, session: AsyncSession) -> User:
    if "@" in user_login.login:
        user: User = await get_user_by_email(user_login.login, session)
    else:
        user: User = await get_user_by_username(user_login.login, session)

    if user is not None and verify_password(user_login.password, user.password_hash):
        return user

    return None


@router.post("/login/")
async def authorization_user(user_login: UserLogin) -> ORJSONResponse:
    async with async_session() as session:
        try:
            authenticated_user = await authorization_by_login(
                user_login,
                session
            )

            if authenticated_user is None:
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
            response.set_cookie('access_token', access_token, secure=True, httponly=True, samesite='strict')
            response.set_cookie('refresh_token', refresh_token, secure=True, httponly=True, samesite='strict')
            return response

        except Exception as e:
            return ORJSONResponse(
                {"msg": f"Ошибка авторизации. {e}"},
                status_code=500
            )


_INVALID_TOKEN_MESSAGE = 'Не удалось авторизоваться по предоставленным данным'


@router.post('/token/')
async def get_user_by_token(access_token: TokenBody) -> ORJSONResponse:
    try:
        payload: dict = decode_token_payload(access_token.token)
        if payload is None or not token_payload_is_access(payload):
            return ORJSONResponse({'msg': _INVALID_TOKEN_MESSAGE}, status_code=401)

        async with async_session() as session:
            user: User = await get_user_by_token_payload(payload, session)

        if user is None:
            return ORJSONResponse({'msg': _INVALID_TOKEN_MESSAGE}, status_code=401)

        user_info = {'id': user.id, 'username': user.username, 'email': user.email, 'created_at': user.created_at,
                     'avatar_path': user.avatar_path}
        return ORJSONResponse(
            {'msg': 'Успешная авторизация',
             'user': user_info},
            status_code=200
        )

    except Exception as e:
        return ORJSONResponse(
            {"msg": f"Ошибка авторизации. {e}"},
            status_code=500
        )


@router.post('/logout/')
async def logout(access_token: str = Cookie(None), refresh_token: str = Cookie(None)):
    access_token_payload = decode_token_payload(access_token)
    refresh_token_payload = decode_token_payload(refresh_token)

    await asyncio.gather(add_token_payload_to_blacklist(access_token_payload),
                         add_token_payload_to_blacklist(refresh_token_payload))

    response = ORJSONResponse({
        'msg': 'Вы успешно вышли из аккаута'},
        status_code=200
    )

    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    return response


@router.post('/refresh/')
async def refresh_access_token(refresh_token: str = Cookie(None)) -> ORJSONResponse:
    try:
        old_token_payload: dict = decode_token_payload(refresh_token)
        if old_token_payload is None:
            raise ValueError('Не удалось валидировать refresh_token')
        if not token_payload_is_refresh(old_token_payload):
            raise ValueError('Это не refresh token')

        async with async_session() as session:
            user: User = await get_user_by_token_payload(old_token_payload, session)

        if user is None:
            raise ValueError("Пользователь не найден")

        new_access_token = create_access_token(create_access_token_payload(user))
        new_refresh_token = create_refresh_token(create_refresh_token_payload(user))

        await add_token_payload_to_blacklist(old_token_payload)

        response = ORJSONResponse(
            {'msg': 'Сгенерированы новые токены'},
            status_code=200
        )

        response.set_cookie('access_token', new_access_token, secure=True, httponly=True, samesite='strict')
        response.set_cookie('refresh_token', new_refresh_token, secure=True, httponly=True, samesite='strict')

        return response

    except Exception as e:
        response = ORJSONResponse({'msg': f'{_INVALID_TOKEN_MESSAGE}: {e}'}, status_code=401)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response


@router.get('/me/')
async def user_get_self(access_token: str = Cookie(None)):
    try:
        if access_token is None:
            raise ValueError('Вы не авторизованы')
        payload: dict = decode_token_payload(access_token)
        if not token_payload_is_access(payload):
            raise ValueError('Это не refresh token')

        async with async_session() as session:
            user: User = await get_user_by_token_payload(payload, session)

        if user is None:
            raise ValueError("Пользователь не найден")

        user_info = {'id': user.id, 'username': user.username, 'email': user.email, 'created_at': user.created_at,
                     'avatar': user.avatar_path}
        return ORJSONResponse({'msg': 'Ваши данные',
                               'user': user_info},
                              status_code=200)

    except Exception as e:
        return ORJSONResponse({'msg': f'{_INVALID_TOKEN_MESSAGE}: {e}'}, status_code=401)
