import jwt

from config import RSA_KEYS
from jwt_tokens.token_generator import ALGORITHM


def decode_token_payload(token: str) -> dict:
    return jwt.decode(token, RSA_KEYS.public_key, algorithms=[ALGORITHM])
