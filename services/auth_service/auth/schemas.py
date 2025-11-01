from pydantic import BaseModel, EmailStr, constr


class UserLogin(BaseModel):
    """
    Модель данных для входа пользователя в систему.
    
    Поддерживает вход как по email, так и по username.
    
    :ivar login: Email или имя пользователя для входа
    :vartype login: EmailStr | constr
    :ivar password: Пароль пользователя
    :vartype password: str
    """
    login: EmailStr | constr(pattern=r'^[a-zA-Z0-9_]{3,32}$')
    password: str


class UserCreate(BaseModel):
    """
    Модель данных для регистрации нового пользователя.
    
    :ivar email: Email пользователя
    :vartype email: EmailStr
    :ivar username: Имя пользователя
    :vartype username: constr
    :ivar password: Пароль пользователя
    :vartype password: str
    """
    email: EmailStr
    username: constr(pattern=r'^[a-zA-Z0-9_]{3,32}$')
    password: str


class TokenBody(BaseModel):
    """
    Модель для передачи JWT токена в теле запроса.
    
    Используется для endpoints, где токен передается не через cookie,
    а непосредственно в теле запроса.
    
    :ivar token: JWT токен (access или refresh)
    :vartype token: str
    """
    token: str


class ChangePassword(BaseModel):
    """
    Модель данных для смены пароля пользователя.
    
    :ivar old_password: Текущий пароль пользователя
    :vartype old_password: str
    :ivar new_password: Новый пароль пользователя
    :vartype new_password: str
    """
    old_password: str
    new_password: str
