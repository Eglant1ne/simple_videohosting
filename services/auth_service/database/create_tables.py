from .base import _Base
from .session import engine


async def create_tables() -> None:
    """
    Асинхронно создает все таблицы в базе данных.

    Выполняет создание всех таблиц, определенных в метаданных SQLAlchemy,
    на основе моделей, унаследованных от _Base. Использует асинхронное
    соединение с базой данных через engine.

    :return: None

    :raises Exception: При ошибках создания таблиц (например, проблемы с подключением к БД)
    """
    async with engine.begin() as conn:
        await conn.run_sync(_Base.metadata.create_all)
