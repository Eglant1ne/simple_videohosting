import uuid

import orjson

from sqlalchemy import update

from .router import router
from .schemas import UnprocessedVideoUploaded, ConfirmVideoHlsConverting

from database.session import async_session
from database.video_info import VideoInfo


@router.publisher("convert_video_to_hls")
@router.subscriber("unprocessed_video_uploaded", group_id="unprocessed_video_uploaded")
async def handle_unprocessed_video_uploaded(info: UnprocessedVideoUploaded) -> bytes:
    video_uuid = uuid.uuid4()
    async with async_session() as session:
        video_info_db = VideoInfo(uuid=video_uuid, author_id=info.user_id)
        session.add(video_info_db)
        await session.commit()

    return orjson.dumps({"video_path": info.video_path, "uuid": video_uuid})


@router.subscriber("confirm_video_hls_converting")
async def confirm_video_hls_converting(info: ConfirmVideoHlsConverting):
    async with async_session() as session:
        await session.execute(
            update(VideoInfo).where(uuid=info.uuid).values(is_complete=True, preview_path=info.preview_path)
        )
        await session.commit()
