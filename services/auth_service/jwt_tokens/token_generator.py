import jwt
import datetime

from config import RSA_KEYS

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 2 * 24
ALGORITHM = "RS256"


def create_access_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    to_encode: dict = data.copy()
    now: datetime.datetime = datetime.datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "nbf": now, "iat": now})
    token = jwt.encode(to_encode, RSA_KEYS.private_key, algorithm=ALGORITHM)
    return token


def create_refresh_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    to_encode: dict = data.copy()
    now: datetime.datetime = datetime.datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update(
        {"exp": expire, "nbf": now, "iat": now})
    token: str = jwt.encode(to_encode, RSA_KEYS.private_key, algorithm=ALGORITHM)
    return token
