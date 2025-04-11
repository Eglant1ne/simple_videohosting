from .user import Base as UserBase
from .session import engine


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
