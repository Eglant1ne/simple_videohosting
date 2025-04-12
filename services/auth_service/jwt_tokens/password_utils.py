from passlib.context import CryptContext


pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_hashed_password(password) -> str:
    return pwd_context.hash(password)
