from pydantic import BaseModel


class UserLogin(BaseModel):
    login: str
    password: str


class UserCreate(BaseModel):
    email: str
    username: str
    password: str
