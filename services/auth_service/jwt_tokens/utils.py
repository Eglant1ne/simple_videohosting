def token_payload_is_access(payload: dict) -> bool:
    """
    Проверяет, является ли payload access токеном.

    :param payload: Словарь с claims JWT токена
    :type payload: dict
    :return: True если токен является access токеном, иначе False
    :rtype: bool
    """
    return payload['token_type'] == 'access'


def token_payload_is_refresh(payload: dict) -> bool:
    """
    Проверяет, является ли payload refresh токеном.

    :param payload: Словарь с claims JWT токена
    :type payload: dict
    :return: True если токен является refresh токеном, иначе False
    :rtype: bool
    """
    return payload['token_type'] == 'refresh'