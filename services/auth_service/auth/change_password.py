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
    """
    Обновляет пароль пользователя в базе данных.
    
    Генерирует хеш нового пароля и увеличивает версию токена для инвалидации
    всех ранее выданных токенов пользователя.
    
    :param user: Объект пользователя, которому меняется пароль
    :type user: User
    :param new_password: Новый пароль в открытом виде
    :type new_password: str
    :param session: Асинхронная сессия базы данных
    :type session: AsyncSession
    :return: None
    
    :Note:
        Увеличение token_version приводит к инвалидации всех существующих
        JWT токенов пользователя, обеспечивая безопасность при смене пароля.
    """
    await session.execute(
        update(User).where(User.id == user.id).values(password_hash=generate_hashed_password(new_password),
                                                      token_version=User.token_version + 1)
    )
    await session.commit()


@router.post('/change_password/')
async def change_password(password_change: ChangePassword, access_token: str = Cookie(None)) -> ORJSONResponse:
    """
    Эндпоинт для изменения пароля текущего авторизованного пользователя.
    
    Проверяет старый пароль, устанавливает новый пароль и инвалидирует
    все текущие токены пользователя путем увеличения token_version.
    После успешной смены пароля удаляет токены из cookies клиента.
    
    :param password_change: Данные для смены пароля (старый и новый пароль)
    :type password_change: ChangePassword
    :param access_token: Access токен из HTTP-only cookie для авторизации
    :type access_token: str
    :return: JSON ответ с результатом операции
    :rtype: ORJSONResponse
    
    :status 200: Пароль успешно изменен
    :status 400: Неправильный старый пароль
    :status 401: Невалидный токен или пользователь не найден
    
    :Raises:
        ValueError: Если токен невалиден или пользователь не существует
    
    :Example:
    
    .. code-block:: json
    
        Request:
        {
            "old_password": "oldPassword123",
            "new_password": "newPassword456"
        }
        
        Response (успех):
        {
            "msg": "Пароль успешно изменён"
        }
        
        Response (ошибка старого пароля):
        {
            "msg": "Неправильный старый пароль"
        }
        
        Response (ошибка авторизации):
        {
            "msg": "Не удалось авторизоваться по предоставленным данным"
        }
    
    :Note:
        После успешной смены пароля все текущие access и refresh токены
        становятся невалидными и пользователь должен авторизоваться заново.
    """
    try:
        # Валидация access токена
        payload: dict = decode_token_payload(access_token)
        if not token_payload_is_access(payload):
            raise ValueError('Это не access token')

        # Получение пользователя по данным из токена
        async with async_session() as session:
            user: User = await get_user_by_token_payload(payload, session)

        if user is None:
            raise ValueError('Пользователь не существует')

    except Exception as e:
        return ORJSONResponse(
            {'msg': f'Не удалось авторизоваться по предоставленным данным'},
            status_code=401)

    # Проверка корректности старого пароля
    if not verify_password(plain_password=password_change.old_password, hashed_password=user.password_hash):
        return ORJSONResponse(
            {'msg': 'Неправильный старый пароль'},
            status_code=400
        )
    
    # Обновление пароля в базе данных
    async with async_session() as session:
        await change_password_db(user=user, new_password=password_change.new_password,
                                 session=session)

    # Создание ответа и удаление токенов из cookies
    response = ORJSONResponse(
        {'msg': 'Пароль успешно изменён'},
        status_code=200
    )
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    return response
