from pydantic import Field
from pydantic_settings import BaseSettings


class DebugMode(BaseSettings):
    """
    Настройки режима отладки приложения.
    
    Определяет включен ли debug-режим для FastAPI приложения.
    В debug-режиме доступны документация и подробные ошибки.
    """
    debug_mode: bool = Field(alias='DEBUG_MODE')


class WorkerThreads(BaseSettings):
    """
    Настройки количества рабочих процессов.
    
    Определяет количество воркеров для Uvicorn сервера.
    Влияет на производительность и параллельную обработку запросов.
    """
    count: int = Field(alias='CHANNEL_ACTIONS_SERVICE_WORKERS')


class DatabaseSettings(BaseSettings):
    """
    Настройки подключения к базе данных PostgreSQL.
    
    Содержит параметры аутентификации и выбора базы данных.
    Используется для подключения к основной БД приложения.
    """
    database: str = Field(alias='POSTGRES_DB')
    user: str = Field(alias='POSTGRES_USER')
    password: str = Field(alias='POSTGRES_PASSWORD')


class RabbitMQSettings(BaseSettings):
    """
    Настройки подключения к RabbitMQ брокеру.
    
    Содержит учетные данные для аутентификации в RabbitMQ.
    Используется для работы с очередями сообщений.
    """
    user: str = Field(alias='RABBITMQ_DEFAULT_USER')
    password: str = Field(alias='RABBITMQ_DEFAULT_PASS')


DEBUG_MODE = DebugMode()
WORKER_THREADS = WorkerThreads()
DATABASE_SETTINGS = DatabaseSettings()
RABBITMQ_SETTINGS = RabbitMQSettings()
