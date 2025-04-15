import uuid
import asyncio

import aiokafka
import orjson

from sqlalchemy import update

from kafka_producer import producer

from database.session import async_session
from database.video_info import VideoInfo

from .schemas import UnprocessedVideoUploaded, ConfirmVideoHlsConverting


async def create_unprocessed_video_consumer():
    try:
        loop = asyncio.get_running_loop()
        consumer = aiokafka.AIOKafkaConsumer("unprocessed_video_uploaded",
                                             loop=loop,
                                             bootstrap_servers='kafka:9092',
                                             enable_auto_commit=False,
                                             group_id='channel_actions')
        await consumer.start()
        async for msg in consumer:
            try:
                data = orjson.loads(msg.value)
                info = UnprocessedVideoUploaded(**data)

                async with async_session() as session:
                    video_info_db = VideoInfo(uuid=uuid.uuid4(), author_id=info.user_id)
                    session.add(video_info_db)
                    await session.commit()

                await producer.send("convert_video_to_hls", orjson.dumps({"video_path": info.video_path}))

                await consumer.commit()
            except Exception:
                pass
    finally:
        await consumer.stop()


async def confirm_video_hls_converting():
    try:
        loop = asyncio.get_running_loop()
        consumer = aiokafka.AIOKafkaConsumer("confirm_video_hls_convertation",
                                             loop=loop,
                                             bootstrap_servers='kafka:9092',
                                             enable_auto_commit=False,
                                             group_id='channel_actions')
        await consumer.start()
        async for msg in consumer:
            data = orjson.loads(msg.value)
            info = ConfirmVideoHlsConverting(**data)

            async with async_session() as session:
                await session.execute(
                    update(VideoInfo).where(uuid=info.uuid).values(is_complete=True, preview_path=info.preview_path)
                )
                await session.commit()

            await consumer.commit()

    finally:
        await consumer.stop()
