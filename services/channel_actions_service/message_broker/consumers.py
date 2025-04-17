import uuid

import orjson

from sqlalchemy import update
from faststream.rabbit import RabbitQueue

from .router import router
from .schemas import UnprocessedVideoUploaded, ConfirmVideoHlsConverting

from database.session import async_session
from database.video_info import VideoInfo

unprocessed_video_uploaded_queue = RabbitQueue("unprocessed_video_uploaded", durable=True, auto_delete=False,
                                               exclusive=False,
                                               arguments={"delivery_mode": 2})

convert_video_to_hls_queue = RabbitQueue("convert_video_to_hls", durable=True, auto_delete=False,
                                         exclusive=False,
                                         arguments={"delivery_mode": 2})

confirm_video_hls_converting_queue = RabbitQueue("confirm_video_hls_converting", durable=True, auto_delete=False,
                                                 exclusive=False,
                                                 arguments={"delivery_mode": 2})


@router.publisher(convert_video_to_hls_queue, persist=True)
@router.subscriber(unprocessed_video_uploaded_queue, retry=True)
async def handle_unprocessed_video_uploaded(info: UnprocessedVideoUploaded) -> bytes:
    video_uuid = uuid.uuid4()
    async with async_session() as session:
        video_info_db = VideoInfo(uuid=video_uuid, author_id=info.user_id)
        session.add(video_info_db)
        await session.commit()

    return orjson.dumps({"video_path": info.video_path, "uuid": video_uuid})


@router.subscriber(confirm_video_hls_converting_queue, retry=True)
async def confirm_video_hls_converting(info: ConfirmVideoHlsConverting):
    async with async_session() as session:
        await session.execute(
            update(VideoInfo).where(VideoInfo.uuid == info.uuid).values(is_complete=True)
        )
        await session.commit()
