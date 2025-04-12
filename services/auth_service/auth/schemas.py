from pydantic import BaseModel, EmailStr, constr


class UserLogin(BaseModel):
    login: EmailStr | constr(pattern=r'^[a-zA-Z0-9_]{3,32}$')
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    username: constr(pattern=r'^[a-zA-Z0-9_]{3,32}$')
    password: str
