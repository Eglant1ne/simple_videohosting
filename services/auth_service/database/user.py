from sqlalchemy import Column, BigInteger, String, TIMESTAMP
from sqlalchemy.sql import func

from .base import _Base


class User(_Base):
    """
    Модель пользователя системы.

    Представляет таблицу 'users' в базе данных и содержит информацию
    об учетных записях пользователей.

    :ivar __tablename__: Название таблицы в базе данных
    :vartype __tablename__: str

    :ivar id: Уникальный идентификатор пользователя (первичный ключ)
    :vartype id: BigInteger
    :ivar username: Уникальное имя пользователя
    :vartype username: String
    :ivar email: Уникальный email адрес пользователя
    :vartype email: String
    :ivar password_hash: Хешированный пароль пользователя
    :vartype password_hash: String
    :ivar created_at: Дата и время создания учетной записи
    :vartype created_at: TIMESTAMP
    :ivar avatar_path: Путь к файлу аватара пользователя
    :vartype avatar_path: String
    :ivar token_version: Версия токена для инвалидации JWT токенов
    :vartype token_version: BigInteger

    :Example:

    .. code-block:: python

        # Создание нового пользователя
        user = User(
            username="john_doe",
            email="john@example.com",
            password_hash="hashed_password_here"
        )

    :Note:
        - Поле ``created_at`` автоматически устанавливается в текущее время при создании записи
        - Поле ``token_version`` используется для принудительной инвалидации всех токенов пользователя
          при смене пароля или выходе из всех устройств
        - Ограничение длины username - 32 символа, email - 254 символа (стандарт RFC)
        - Все строковые поля имеют явное указание name для соответствия naming convention
    """
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, index=True, name='id')
    username = Column(String(32), unique=True, index=True, nullable=False, name='username')
    email = Column(String(254), unique=True, index=True, nullable=False, name='email')
    password_hash = Column(String, nullable=False, name='password_hash')
    created_at = Column(TIMESTAMP, server_default=func.now(), name='created_at')
    avatar_path = Column(String, nullable=True, name='avatar_path')
    token_version = Column(BigInteger, nullable=False, name='token_version', server_default='0')
