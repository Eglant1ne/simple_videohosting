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
    """
    Аутентифицирует пользователя по логину и паролю.
    
    Определяет тип логина (email или username) по наличию символа '@' 
    и проверяет соответствие пароля.
    
    :param user_login: Данные для входа пользователя
    :type user_login: UserLogin
    :param session: Асинхронная сессия базы данных
    :type session: AsyncSession
    :return: Аутентифицированный пользователь или None если аутентификация не удалась
    :rtype: User or None
    
    :Example:
    
    .. code-block:: python
    
        user_login = UserLogin(login="user@example.com", password="password")
        user = await authorization_by_login(user_login, session)
    """
    if "@" in user_login.login:
        user: User = await get_user_by_email(user_login.login, session)
    else:
        user: User = await get_user_by_username(user_login.login, session)

    if user is not None and verify_password(user_login.password, user.password_hash):
        return user

    return None


@router.post("/login/")
async def authorization_user(user_login: UserLogin) -> ORJSONResponse:
    """
    Эндпоинт для авторизации пользователя в системе.
    
    Принимает логин и пароль, проверяет их корректность и в случае успешной
    аутентификации устанавливает access и refresh токены в HTTP-only cookies.
    
    :param user_login: Данные для входа пользователя
    :type user_login: UserLogin
    :return: JSON ответ с результатом операции
    :rtype: ORJSONResponse
    
    :status 200: Успешная авторизация
    :status 401: Неверная почта/имя пользователя или пароль
    :status 500: Внутренняя ошибка сервера
    
    :Example:
    
    .. code-block:: json
    
        Request:
        {
            "login": "user@example.com",
            "password": "password123"
        }
        
        Response:
        {
            "msg": "Успешная авторизация."
        }
    """
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
    """
    Эндпоинт для получения информации о пользователе по access токену.
    
    Валидирует access токен, извлекает payload и возвращает данные пользователя.
    Токен передается в теле запроса.
    
    :param access_token: Access токен в теле запроса
    :type access_token: TokenBody
    :return: JSON ответ с данными пользователя или ошибкой
    :rtype: ORJSONResponse
    
    :status 200: Успешная авторизация, возвращены данные пользователя
    :status 401: Невалидный токен или пользователь не найден
    :status 500: Внутренняя ошибка сервера
    
    :Example:
    
    .. code-block:: json
    
        Request:
        {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
        
        Response:
        {
            "msg": "Успешная авторизация",
            "user": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "created_at": "2023-01-01T00:00:00",
                "avatar_path": "/avatars/1.jpg"
            }
        }
    """
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
    """
    Эндпоинт для выхода пользователя из системы.
    
    Добавляет текущие access и refresh токены в черный список Redis
    и удаляет их из cookies клиента.
    
    :param access_token: Access токен из HTTP-only cookie (опционально)
    :type access_token: str
    :param refresh_token: Refresh токен из HTTP-only cookie (опционально)
    :type refresh_token: str
    :return: JSON ответ с результатом выхода
    :rtype: ORJSONResponse
    
    :status 200: Успешный выход из системы
    
    :Note:
        Токены извлекаются из cookies автоматически FastAPI с помощью декоратора Cookie
    """
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
    """
    Эндпоинт для обновления access токена с помощью refresh токена.
    
    Валидирует refresh токен, генерирует новую пару токенов (access и refresh),
    добавляет старый refresh токен в черный список и устанавливает новые токены в cookies.
    
    :param refresh_token: Refresh токен из HTTP-only cookie (опционально)
    :type refresh_token: str
    :return: JSON ответ с результатом обновления токенов
    :rtype: ORJSONResponse
    
    :status 200: Токены успешно обновлены
    :status 401: Невалидный refresh токен или пользователь не найден
    
    :Raises:
        ValueError: Если токен невалиден или пользователь не найден
    
    :Example:
    
    .. code-block:: json
    
        Response (успех):
        {
            "msg": "Сгенерированы новые токены"
        }
        
        Response (ошибка):
        {
            "msg": "Не удалось авторизоваться по предоставленным данным: ..."
        }
    """
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
    """
    Эндпоинт для получения информации о текущем авторизованном пользователе.
    
    Извлекает access токен из cookie, валидирует его и возвращает данные
    пользователя, ассоциированного с этим токеном.
    
    :param access_token: Access токен из HTTP-only cookie (опционально)
    :type access_token: str
    :return: JSON ответ с данными пользователя или ошибкой
    :rtype: ORJSONResponse
    
    :status 200: Успешно возвращены данные пользователя
    :status 401: Пользователь не авторизован или токен невалиден
    
    :Example:
    
    .. code-block:: json
    
        Response:
        {
            "msg": "Ваши данные",
            "user": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "created_at": "2023-01-01T00:00:00",
                "avatar": "/avatars/1.jpg"
            }
        }
    """
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
