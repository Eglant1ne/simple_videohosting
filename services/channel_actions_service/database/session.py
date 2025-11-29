from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import DATABASE_SETTINGS


DATABASE_URL: str = f"postgresql+asyncpg://{DATABASE_SETTINGS.user}:{DATABASE_SETTINGS.password}@postgres/" \
               f"{DATABASE_SETTINGS.database}"
"""
URL подключения к базе данных PostgreSQL.

Формируется из настроек подключения:
- Логин и пароль из DATABASE_SETTINGS
- Хост: postgres (имя сервиса в Docker)
- Имя базы данных из DATABASE_SETTINGS

Использует асинхронный драйвер asyncpg для высокопроизводительных операций.
"""

engine = create_async_engine(DATABASE_URL, echo=False)
"""
Асинхронный движок SQLAlchemy для подключения к базе данных.

:param echo: Отключен вывод SQL запросов в консоль для production
:type echo: bool

Движок управляет пулом подключений и выполняет основные операции с БД.
"""

async_session: AsyncSession = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
"""
Фабрика асинхронных сессий для работы с базой данных.

:param bind: Привязка к движку базы данных
:param class_: Класс асинхронной сессии
:param expire_on_commit: Отключение автоматического expire после коммита

Позволяет создавать сессии для выполнения запросов к базе данных.
"""
