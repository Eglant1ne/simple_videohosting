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
    count: int = Field(alias='VIDEO_POSTPROCESS_WORKERS')


class RabbitMQSettings(BaseSettings):
    """
    Настройки подключения к RabbitMQ брокеру.
    
    Содержит учетные данные для аутентификации в RabbitMQ.
    Используется для работы с очередями сообщений.
    """
    user: str = Field(alias='RABBITMQ_DEFAULT_USER')
    password: str = Field(alias='RABBITMQ_DEFAULT_PASS')
    host: str = Field(default='rabbitmq', alias='RABBITMQ_HOST')
    port: int = Field(default=5672, alias='RABBITMQ_PORT')

    @property
    def url(self) -> str:
        """URL для подключения к RabbitMQ."""
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"


class MinIOSettings(BaseSettings):
    """
    Настройки подключения к MinIO/S3 хранилищу.
    
    Содержит параметры для доступа к объектному хранилищу.
    Используется для загрузки и выгрузки видео файлов.
    """
    bucket: str = Field(default='files', alias='S3_BUCKET')
    region: str = Field(default='us-east-1', alias='S3_REGION')
    endpoint: str = Field(alias='MINIO_SERVER_URL')
    access_key: str = Field(alias='MINIO_ROOT_USER')
    secret_key: str = Field(alias='MINIO_ROOT_PASSWORD')
    timeout: int = Field(default=30, alias='MINIO_STALE_UPLOADS_EXPIRY')

    @property
    def endpoint_url(self) -> str:
        """URL endpoint с протоколом."""
        endpoint = self.endpoint
        if not endpoint:
            return "http://localhost:9000"
        
        # Убираем возможные дублирования протокола
        if endpoint.startswith('http://http://') or endpoint.startswith('https://https://'):
            endpoint = endpoint[7:]  # убираем первый http://
        
        # Добавляем протокол если отсутствует
        if not endpoint.startswith(('http://', 'https://')):
            endpoint = f"http://{endpoint}"
            
        return endpoint


class ServerSettings(BaseSettings):
    """
    Настройки сервера приложения.
    
    Определяет хост и порт для запуска FastAPI приложения.
    """
    host: str = Field(default='0.0.0.0', alias='SERVER_HOST')
    port: int = Field(default=8090, alias='SERVER_PORT')


DEBUG_MODE = DebugMode()
WORKER_THREADS = WorkerThreads()
RABBITMQ_SETTINGS = RabbitMQSettings()
MINIO_SETTINGS = MinIOSettings()
SERVER_SETTINGS = ServerSettings()