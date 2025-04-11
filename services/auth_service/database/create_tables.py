from .user import _Base
from .session import engine


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(_Base.metadata.create_all)
