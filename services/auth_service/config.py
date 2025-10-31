from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    database: str = Field(alias='POSTGRES_DB')
    user: str = Field(alias='POSTGRES_USER')
    password: str = Field(alias='POSTGRES_PASSWORD')


class RedisSettings(BaseSettings):
    password: str = Field(alias='REDIS_PASSWORD')


class DebugMode(BaseSettings):
    debug_mode: bool = Field(alias='DEBUG_MODE')


class WorkerThreads(BaseSettings):
    count: int = Field(alias='AUTH_SERVICE_WORKERS')


class RSAKeys(BaseSettings):
    public_key: str = Field(alias="RSA_PUBLIC_KEY")
    private_key: str = Field(alias="RSA_PRIVATE_KEY")


DATABASE_SETTINGS: DatabaseSettings = DatabaseSettings()
DEBUG_MODE: DebugMode = DebugMode()
RSA_KEYS: RSAKeys = RSAKeys()
WORKER_THREADS: WorkerThreads = WorkerThreads()
REDIS_SETTINGS: RedisSettings = RedisSettings()
