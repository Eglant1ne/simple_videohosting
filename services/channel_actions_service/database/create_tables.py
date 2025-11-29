from .base import _Base
from .session import engine


async def create_tables() -> None:
    """
    Асинхронная функция для создания таблиц в базе данных.
    
    Выполняет создание всех таблиц, определенных в метаданных SQLAlchemy.
    Используется при инициализации приложения для подготовки БД.
    
    :return: None
    :rtype: None
    
    **Примечания:**
    
    - Создает только отсутствующие таблицы
    - Не выполняет миграции существующих таблиц
    - Использует асинхронное подключение к базе данных
    """
    async with engine.begin() as conn:
        await conn.run_sync(_Base.metadata.create_all)
