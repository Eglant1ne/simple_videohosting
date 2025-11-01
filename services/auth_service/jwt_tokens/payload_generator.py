import uuid

from database.user import User


def create_access_token_payload(user: User) -> dict:
    """
    Создает payload для access JWT токена.

    Формирует словарь с claims для access токена, который используется
    для аутентификации пользователя при доступе к защищенным ресурсам.

    :param user: Объект пользователя для которого создается токен
    :type user: User
    :return: Словарь с claims access токена
    :rtype: dict

    :Example:

    .. code-block:: python

        user = User(id=123, token_version=1)
        payload = create_access_token_payload(user)
        # payload = {
        #     "sub": "123",
        #     "jti": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        #     "version": "1",
        #     "token_type": "access"
        # }

    :Note:
        - ``sub`` (subject) - идентификатор пользователя
        - ``jti`` (JWT ID) - уникальный идентификатор токена
        - ``version`` - версия токена для инвалидации при смене пароля
        - ``token_type`` - тип токена ("access" для access токена)
    """
    payload: dict = dict()
    payload["sub"] = str(user.id)
    payload["jti"] = str(uuid.uuid4())
    payload["version"] = str(user.token_version)
    payload["token_type"] = "access"

    return payload


def create_refresh_token_payload(user: User) -> dict:
    """
    Создает payload для refresh JWT токена.

    Формирует словарь с claims для refresh токена, который используется
    для получения новой пары access/refresh токенов без повторной аутентификации.

    :param user: Объект пользователя для которого создается токен
    :type user: User
    :return: Словарь с claims refresh токена
    :rtype: dict

    :Example:

    .. code-block:: python

        user = User(id=123, token_version=1)
        payload = create_refresh_token_payload(user)
        # payload = {
        #     "sub": "123",
        #     "jti": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
        #     "version": "1",
        #     "token_type": "refresh"
        # }

    :Note:
        - ``sub`` (subject) - идентификатор пользователя
        - ``jti`` (JWT ID) - уникальный идентификатор токена
        - ``version`` - версия токена для инвалидации при смене пароля
        - ``token_type`` - тип токена ("refresh" для refresh токена)
        - Refresh токены обычно имеют больший срок жизни чем access токены
    """
    payload: dict = dict()
    payload["sub"] = str(user.id)
    payload["jti"] = str(uuid.uuid4())
    payload["version"] = str(user.token_version)
    payload["token_type"] = "refresh"

    return payload
