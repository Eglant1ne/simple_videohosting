import jwt
import datetime

from config import RSA_KEYS


ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "RS256"


def create_access_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, RSA_KEYS.private_key, algorithm=ACCESS_TOKEN_EXPIRE_MINUTES)
    return token

