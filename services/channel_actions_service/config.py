from pydantic import Field
from pydantic_settings import BaseSettings


class DebugMode(BaseSettings):
    debug_mode: bool = Field(alias='DEBUG_MODE')


class WorkerThreads(BaseSettings):
    count: int = Field(alias='CHANNEL_ACTIONS_SERVICE_WORKERS')


class DatabaseSettings(BaseSettings):
    database: str = Field(alias='POSTGRES_DB')
    user: str = Field(alias='POSTGRES_USER')
    password: str = Field(alias='POSTGRES_PASSWORD')


DEBUG_MODE = DebugMode()
WORKER_THREADS = WorkerThreads()
DATABASE_SETTINGS = DatabaseSettings()
