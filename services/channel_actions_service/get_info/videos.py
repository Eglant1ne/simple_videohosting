import uuid

import orjson
from pydantic import conint

from fastapi.responses import ORJSONResponse

from .router import router

from sqlalchemy import select

from database.video_info import VideoInfo
from database.session import async_session


@router.get('videos/author/{author_id}')
async def get_author_videos(author_id: int, offset: conint(ge=0) = 0,
                            count: conint(ge=1, le=100) = 100) -> ORJSONResponse:
    async with async_session() as session:
        result = await session.execute(
            select(VideoInfo).where(VideoInfo.author_id == author_id).limit(count).offset(offset)
        )
        result = result.scalars().all()
        return ORJSONResponse({'msg': 'Видео успешно выбраны',
                               'videos': result})
