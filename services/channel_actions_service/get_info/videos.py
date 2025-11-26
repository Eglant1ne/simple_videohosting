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
    """
    Получение списка видео конкретного автора с пагинацией.
    
    .. note::
        Возвращает только полностью обработанные видео (is_complete = True)
    
    :param author_id: ID автора для фильтрации видео
    :type author_id: int
    :param offset: Смещение для пагинации (по умолчанию 0)
    :type offset: int
    :param count: Количество возвращаемых видео (1-20, по умолчанию 20)
    :type count: int
    :return: JSON ответ со списком видео автора
    :rtype: ORJSONResponse
    :raises: 500 Internal Server Error при ошибках БД
    """
    async with async_session() as session:
        # Выполняем запрос к БД с фильтрацией по автору и статусу обработки
        result = await session.execute(
            select(VideoInfo).where(VideoInfo.author_id == author_id, VideoInfo.is_complete == True).limit(
                count).offset(offset)
        )
        result = result.scalars().all()
        return ORJSONResponse({'msg': 'Видео успешно выбраны',
                               'videos': [video.to_dict() for video in result]})


@router.get('/videos/batch')
async def get_author_videos(offset: conint(ge=0) = 0, count: conint(ge=1, le=20) = 20) -> ORJSONResponse:
    """
    Получение батча обработанных видео с пагинацией.

    :param offset: Смещение для пагинации (по умолчанию 0)
    :type offset: int
    :param count: Количество возвращаемых видео (1-20, по умолчанию 20)
    :type count: int
    :return: JSON ответ со списком видео
    :rtype: ORJSONResponse
    """
    async with async_session() as session:
        result = await session.execute(
            select(VideoInfo).where(VideoInfo.is_complete == True).limit(count).offset(offset)
        )
        result = result.scalars().all()
        return ORJSONResponse({'msg': 'Видео успешно выбраны',
                               'videos': result})


@router.get('/video/')
async def get_author_videos(uuid: UUID4) -> ORJSONResponse:
    """
    Получение детальной информации о конкретном видео по UUID.
    
    .. note::
        Возвращает 503 ошибку если видео еще не обработано
    
    :param uuid: UUID видео для поиска
    :type uuid: UUID4
    :return: Детальная информация о видео
    :rtype: ORJSONResponse
    :raises: 503 Service Unavailable если видео не обработано
    """
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
    Получение списка всех видео с расширенной пагинацией.

    :param page: Номер страницы (начинается с 1)
    :type page: int
    :param page_size: Размер страницы (1-100 видео)
    :type page_size: int
    :return: Список видео с метаданными пагинации
    :rtype: dict
    :raises: 500 Internal Server Error при ошибках БД
    """
    try:
        async with async_session() as session:
            # Получаем общее количество видео для расчета пагинации
            total_count = await session.scalar(
                select(func.count(VideoInfo.uuid))
            )
            
            # Рассчитываем смещение для SQL запроса
            offset = (page - 1) * page_size
            
            # Формируем запрос с сортировкой по дате создания и пагинацией
            stmt = (
                select(VideoInfo)
                .order_by(VideoInfo.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            
            result = await session.execute(stmt)
            videos = result.scalars().all()
                        
            # Конвертируем объекты VideoInfo в словари
            videos_data = [video.to_dict() for video in videos]
            
            # Возвращаем ответ с полной информацией о пагинации
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
        # Ловим любые исключения и возвращаем 500 ошибку
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при получении видео: {str(e)}"
        )
