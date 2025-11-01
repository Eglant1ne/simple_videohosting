from fastapi import APIRouter

# Роутер для управления аутентификацией и авторизацией пользователей.
router = APIRouter(prefix='/auth', tags=['Auth'])