import asyncio
import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI

from handlers.health import router as health_router
from services.video_processor import VideoProcessor

from config import DEBUG_MODE, WORKER_THREADS, SERVER_SETTINGS, RABBITMQ_SETTINGS, MINIO_SETTINGS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    
    Выполняет инициализацию и завершение работы видео процессора.
    Запускает потребителей RabbitMQ при старте приложения.
    """
    video_processor = VideoProcessor(RABBITMQ_SETTINGS, MINIO_SETTINGS)
    await video_processor.start()
    yield
    await video_processor.stop()


app = FastAPI(
    docs_url='/docs' if DEBUG_MODE.debug_mode else None,
    redoc_url='/redoc' if DEBUG_MODE.debug_mode else None,
    lifespan=lifespan
)

app.include_router(health_router)


async def main():
    """
    Основная асинхронная функция для инициализации приложения.
    
    Может использоваться для дополнительной инициализации перед запуском сервера.
    """
    pass


if __name__ == '__main__':
    """
    Точка входа при запуске приложения напрямую.
    
    Запускает инициализацию и стартует Uvicorn сервер.
    Настройки сервера:
    - Хост: из конфигурации SERVER_SETTINGS
    - Порт: из конфигурации SERVER_SETTINGS  
    - Количество воркеров: из конфигурации WORKER_THREADS
    - Режим перезагрузки: из конфигурации DEBUG_MODE
    """
    asyncio.run(main())
    uvicorn.run(
        "main:app",
        host=SERVER_SETTINGS.host,
        port=SERVER_SETTINGS.port,
        workers=WORKER_THREADS.count,
        reload=DEBUG_MODE.debug_mode
    )
