import uuid

import orjson

from sqlalchemy import update
from faststream.rabbit import RabbitQueue

from .router import router
from .schemas import UnprocessedVideoUploaded, ConfirmVideoHlsConverting

from database.session import async_session
from database.video_info import VideoInfo

# Очередь для получения событий о загруженном необработанном видео
unprocessed_video_uploaded_queue = RabbitQueue("unprocessed_video_uploaded", durable=True, auto_delete=False,
                                               exclusive=False,
                                               arguments={"delivery_mode": 2})

# Очередь для отправки видео на конвертацию в HLS формат
convert_video_to_hls_queue = RabbitQueue("convert_video_to_hls", durable=True, auto_delete=False,
                                         exclusive=False,
                                         arguments={"delivery_mode": 2})

# Очередь для подтверждения успешной конвертации видео в HLS
confirm_video_hls_converting_queue = RabbitQueue("confirm_video_hls_converting", durable=True, auto_delete=False,
                                                 exclusive=False,
                                                 arguments={"delivery_mode": 2})


@router.publisher(convert_video_to_hls_queue, persist=True)
@router.subscriber(unprocessed_video_uploaded_queue, retry=True)
async def handle_unprocessed_video_uploaded(info: UnprocessedVideoUploaded) -> bytes:
    """
    Обработчик события загрузки необработанного видео.
    
    .. note::
        Этот обработчик является одновременно подписчиком и издателем
        
    :param info: Данные о загруженном видео
    :type info: UnprocessedVideoUploaded
    :return: Сериализованные данные для конвертации видео
    :rtype: bytes
    
    **Процесс обработки:**
    
    1. Создает новый UUID для видео
    2. Сохраняет запись о видео в базу данных
    3. Отправляет сообщение в очередь конвертации
    """
    video_uuid = uuid.uuid4()
    
    async with async_session() as session:
        video_info_db = VideoInfo(uuid=video_uuid, author_id=info.user_id)
        session.add(video_info_db)
        await session.commit()

    return orjson.dumps({"video_path": info.video_path, "uuid": video_uuid})


@router.subscriber(confirm_video_hls_converting_queue, retry=True)
async def confirm_video_hls_converting(info: ConfirmVideoHlsConverting):
    """
    Обработчик подтверждения успешной конвертации видео в HLS формат.
    
    :param info: Данные о конвертированном видео
    :type info: ConfirmVideoHlsConverting
    
    **Процесс обработки:**
    
    1. Обновляет статус видео в базе данных на "обработано"
    2. Устанавливает флаг is_complete = True
    
    **Примечания:**
    
    - После выполнения этой функции видео становится доступным для просмотра
    - Обработчик автоматически повторяет попытку при ошибках (retry=True)
    """
    async with async_session() as session:
        await session.execute(
            update(VideoInfo).where(VideoInfo.uuid == info.uuid).values(is_complete=True)
        )
        await session.commit()
