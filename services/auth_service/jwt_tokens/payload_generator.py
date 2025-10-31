import uuid

from database.user import User


def create_access_token_payload(user: User) -> dict:
    payload: dict = dict()
    payload["sub"] = str(user.id)
    payload["jti"] = str(uuid.uuid4())
    payload["version"] = str(user.token_version)
    payload["token_type"] = "access"

    return payload


def create_refresh_token_payload(user: User) -> dict:
    payload: dict = dict()
    payload["sub"] = str(user.id)
    payload["jti"] = str(uuid.uuid4())
    payload["version"] = str(user.token_version)
    payload["token_type"] = "refresh"

    return payload
