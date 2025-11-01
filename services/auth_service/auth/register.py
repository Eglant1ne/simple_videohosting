from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import async_session
from database.user import User

from .router import router
from .schemas import UserCreate
from .utils import get_user_by_email, get_user_by_username, generate_hashed_password


async def create_user(user: UserCreate, session: AsyncSession) -> User:
    """
    Создает нового пользователя в базе данных.
    
    Генерирует хеш пароля и сохраняет данные пользователя в базе данных.
    
    :param user: Данные для создания пользователя
    :type user: UserCreate
    :param session: Асинхронная сессия базы данных
    :type session: AsyncSession
    :return: Созданный объект пользователя
    :rtype: User
    
    :raises Exception: При ошибках работы с базой данных
    """
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
    """
    Эндпоинт для регистрации нового пользователя.
    
    Проверяет уникальность email и username, затем создает нового пользователя
    в системе. Пароль хешируется перед сохранением в базу данных.
    
    :param user: Данные для регистрации пользователя
    :type user: UserCreate
    :return: JSON ответ с результатом регистрации
    :rtype: ORJSONResponse
    
    :status 200: Успешная регистрация
    :status 400: Почта или имя пользователя уже заняты
    :status 500: Внутренняя ошибка сервера при регистрации
    
    :Example:
    
    .. code-block:: json
    
        Request:
        {
            "email": "user@example.com",
            "username": "newuser",
            "password": "securepassword123"
        }
        
        Response (успех):
        {
            "msg": "Успешно."
        }
        
        Response (почта занята):
        {
            "msg": "Почта уже зарегистрирована."
        }
        
        Response (имя занято):
        {
            "msg": "Аккаунт с таким именем уже существует."
        }
        
        Response (ошибка сервера):
        {
            "msg": "Ошибка регистрации!"
        }
    
    :Note:
        Пароль пользователя хешируется перед сохранением в базу данных
        для обеспечения безопасности.
    """
    async with async_session() as session:
        try:
            # Проверка уникальности email
            if await get_user_by_email(user.email, session):
                return ORJSONResponse(
                    {"msg": "Почта уже зарегистрирована."},
                    status_code=400,
                )
            
            # Проверка уникальности username
            if await get_user_by_username(user.username, session):
                return ORJSONResponse(
                    {"msg": "Аккаунт с таким именем уже существует."},
                    status_code=400,
                )

            # Создание пользователя
            await create_user(user, session)
            return ORJSONResponse(
                {"msg": "Успешно."},
                status_code=200
            )

        except Exception:
            # Откат транзакции в случае ошибки
            await session.rollback()
            return ORJSONResponse({"msg": "Ошибка регистрации!"},
                                  status_code=500,
                                  )
