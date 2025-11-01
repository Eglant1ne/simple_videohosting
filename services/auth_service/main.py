import asyncio
import uvicorn
import healthcheck
import database

from fastapi import FastAPI

from auth import router as auth_router

from config import DEBUG_MODE, WORKER_THREADS

# Создание экземпляра FastAPI приложения
app = FastAPI(
    docs_url='/docs' if DEBUG_MODE.debug_mode else None,
    redoc_url='/redoc' if DEBUG_MODE.debug_mode else None
)
"""
Основное приложение FastAPI.

Инициализируется с конфигурацией в зависимости от режима отладки.
Автогенерируемая документация доступна только в debug режиме.

:var app: Экземпляр FastAPI приложения
:type app: FastAPI

:Note:
    - Документация Swagger (/docs) и ReDoc (/redoc) отключаются в production
    - Это повышает безопасность и снижает информационную раскрытость
"""

# Подключение роутеров
app.include_router(healthcheck.router)
"""Подключение роутера health-check эндпоинтов."""

app.include_router(auth_router.router)
"""Подключение роутера аутентификации и авторизации."""


async def main():
    """
    Основная асинхронная функция инициализации приложения.

    Выполняет подготовительные операции перед запуском сервера:
    - Создание таблиц в базе данных (если они не существуют)

    :return: None

    :raises Exception: При ошибках создания таблиц в базе данных

    :Note:
        - В production среде рекомендуется использовать миграции вместо создания таблиц
        - Функция выполняется один раз при запуске приложения
    """
    await database.create_tables.create_tables()


if __name__ == '__main__':
    """
    Точка входа при запуске скрипта напрямую.

    Запускает инициализацию приложения и сервер Uvicorn.
    
    :Note:
        - Используется asyncio для асинхронного запуска инициализации
        - Uvicorn запускается с конфигурацией из настроек приложения
        - Workers настроены на основе WORKER_THREADS.count для горизонтального масштабирования
        - Reload отключен для production использования
    """
    asyncio.run(main())
    uvicorn.run(
        "main:app",
        host='0.0.0.0',
        port=8000,
        workers=WORKER_THREADS.count,
        reload=False
    )
