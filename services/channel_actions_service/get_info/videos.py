from pydantic import conint, UUID4

from fastapi.responses import ORJSONResponse
from fastapi import Query, HTTPException

from .router import router

from sqlalchemy import select, func

from database.video_info import VideoInfo
from database.session import async_session


@router.get('/videos/author/{author_id}')
async def get_author_videos(author_id: int, offset: conint(ge=0) = 0,
                            count: conint(ge=1, le=20) = 20) -> ORJSONResponse:
    async with async_session() as session:
        result = await session.execute(
            select(VideoInfo).where(VideoInfo.author_id == author_id, VideoInfo.is_complete == True).limit(
                count).offset(offset)
        )
        result = result.scalars().all()
        return ORJSONResponse({'msg': 'Видео успешно выбраны',
                               'videos': [video.to_dict() for video in result]})


@router.get('/videos/batch')
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

@router.get('/videos/')
async def get_all_videos(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы")
):
    """
    Получение списка всех видео с пагинацией
    """
    try:
        async with async_session() as session:
            # Общее количество видео
            total_count = await session.scalar(
                select(func.count(VideoInfo.uuid))
            )
            
            offset = (page - 1) * page_size
            stmt = (
                select(VideoInfo)
                .order_by(VideoInfo.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            
            result = await session.execute(stmt)
            videos = result.scalars().all()
                        
            videos_data = [video.to_dict() for video in videos]
            
            return {
                "msg": "Видео успешно получены",
                "videos": videos_data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1,
                    "has_next": page * page_size < total_count,
                    "has_prev": page > 1
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при получении видео: {str(e)}"
        )
