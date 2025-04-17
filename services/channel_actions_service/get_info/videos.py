from pydantic import conint, UUID4

from fastapi.responses import ORJSONResponse

from .router import router

from sqlalchemy import select

from database.video_info import VideoInfo
from database.session import async_session


@router.get('videos/author/{author_id}')
async def get_author_videos(author_id: int, offset: conint(ge=0) = 0,
                            count: conint(ge=1, le=20) = 20) -> ORJSONResponse:
    async with async_session() as session:
        result = await session.execute(
            select(VideoInfo).where(VideoInfo.author_id == author_id, VideoInfo.is_complete == True).limit(
                count).offset(offset)
        )
        result = result.scalars().all()
        return ORJSONResponse({'msg': 'Видео успешно выбраны',
                               'videos': result})


@router.get('videos/batch')
async def get_author_videos(offset: conint(ge=0) = 0, count: conint(ge=1, le=20) = 20) -> ORJSONResponse:
    async with async_session() as session:
        result = await session.execute(
            select(VideoInfo).where(VideoInfo.is_complete == True).limit(count).offset(offset)
        )
        result = result.scalars().all()
        return ORJSONResponse({'msg': 'Видео успешно выбраны',
                               'videos': result})


@router.get('/video/')
async def get_author_videos(uuid: UUID4) -> ORJSONResponse:
    async with async_session() as session:
        result = await session.execute(
            select(VideoInfo).where(VideoInfo.uuid == uuid))
        result: VideoInfo = result.scalars().first()
        if not result.is_complete:
            return ORJSONResponse({"msg": "Видео не обработано"}, status_code=503)
        result_info = {"uuid": str(result.uuid), "author_id": result.author_id, "created_at": result.created_at,
                       "likes_count": result.likes_count, "dislikes_count": result.dislikes_count,
                       "views_count": result.views_count}
        return ORJSONResponse({'msg': 'Видео успешно выбраны',
                               "video_info": result_info})
