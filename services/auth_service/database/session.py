from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import DATABASE_SETTINGS


DATABASE_URL: str = f"postgresql+asyncpg://{DATABASE_SETTINGS.user}:{DATABASE_SETTINGS.password}@postgres/" \
               f"{DATABASE_SETTINGS.database}"
engine = create_async_engine(DATABASE_URL, echo=False)

async_session: AsyncSession = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
