from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """
    Настройки подключения к PostgreSQL базе данных.

    :ivar database: Название базы данных
    :vartype database: str
    :ivar user: Имя пользователя для подключения к БД
    :vartype user: str
    :ivar password: Пароль для подключения к БД
    :vartype password: str
    """
    database: str = Field(alias='POSTGRES_DB')
    user: str = Field(alias='POSTGRES_USER')
    password: str = Field(alias='POSTGRES_PASSWORD')


class RedisSettings(BaseSettings):
    """
    Настройки подключения к Redis.

    :ivar password: Пароль для аутентификации в Redis
    :vartype password: str
    """
    password: str = Field(alias='REDIS_PASSWORD')


class DebugMode(BaseSettings):
    """
    Настройки режима отладки приложения.

    :ivar debug_mode: Флаг включения/выключения режима отладки
    :vartype debug_mode: bool
    """
    debug_mode: bool = Field(alias='DEBUG_MODE')


class WorkerThreads(BaseSettings):
    """
    Настройки количества рабочих процессов сервиса аутентификации.

    :ivar count: Количество рабочих процессов/потоков
    :vartype count: int
    """
    count: int = Field(alias='AUTH_SERVICE_WORKERS')


class RSAKeys(BaseSettings):
    """
    Настройки RSA ключей для JWT токенов.

    :ivar public_key: Публичный RSA ключ для верификации JWT токенов
    :vartype public_key: str
    :ivar private_key: Приватный RSA ключ для подписи JWT токенов
    :vartype private_key: str
    """
    public_key: str = Field(alias="RSA_PUBLIC_KEY")
    private_key: str = Field(alias="RSA_PRIVATE_KEY")


# Глобальные экземпляры настроек
DATABASE_SETTINGS: DatabaseSettings = DatabaseSettings()
"""Глобальный экземпляр настроек базы данных."""

DEBUG_MODE: DebugMode = DebugMode()
"""Глобальный экземпляр настроек режима отладки."""

RSA_KEYS: RSAKeys = RSAKeys()
"""Глобальный экземпляр настроек RSA ключей."""

WORKER_THREADS: WorkerThreads = WorkerThreads()
"""Глобальный экземпляр настроек рабочих процессов."""

REDIS_SETTINGS: RedisSettings = RedisSettings()
"""Глобальный экземпляр настроек Redis."""

"""
Конфигурация приложения.

Все настройки загружаются из переменных окружения с использованием
соответствующих алиасов. Pydantic автоматически обрабатывает парсинг
и валидацию значений.

:Note:
    - Для работы необходимо установить соответствующие переменные окружения
    - Pydantic автоматически ищет переменные в .env файле и окружении процесса
    - Все настройки являются синглтонами и инициализируются при импорте модуля
"""
