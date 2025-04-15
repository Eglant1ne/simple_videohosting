import uuid
import asyncio

import aiokafka
import orjson

from .schemas import UnprocessedVideoUploaded

from kafka_producer import producer

from database.session import async_session
from database.video_info import VideoInfo


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
                data = orjson.loads(msg.value.decode('utf-8'))
                info = UnprocessedVideoUploaded(**data)

                async with async_session() as session:
                    try:
                        video_info_db = VideoInfo(uuid=uuid.uuid4(), author_id=info.user_id)
                        session.add(video_info_db)
                        await session.commit()
                    except Exception:
                        await session.rollback()

                await producer.send("convert_video_to_hls", orjson.dumps({"video_path": info.video_path}))

                await consumer.commit()
            except Exception:
                pass
    finally:
        await consumer.stop()
