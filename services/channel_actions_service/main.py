import asyncio
import uvicorn

import healthcheck
import get_info

import database

from contextlib import asynccontextmanager

from fastapi import FastAPI

from faststream.rabbit import RabbitBroker

from message_broker.router import router as broker_router
from message_broker.router import rabbitmq_url

from config import DEBUG_MODE, WORKER_THREADS

from message_broker.consumers import unprocessed_video_uploaded_queue, convert_video_to_hls_queue, \
    confirm_video_hls_converting_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    rabbitmq_broker = RabbitBroker(rabbitmq_url)
    await rabbitmq_broker.connect()
    await rabbitmq_broker.declare_queue(unprocessed_video_uploaded_queue)
    await rabbitmq_broker.declare_queue(convert_video_to_hls_queue)
    await rabbitmq_broker.declare_queue(confirm_video_hls_converting_queue)
    await rabbitmq_broker.close()
    yield


app = FastAPI(docs_url='/docs' if DEBUG_MODE.debug_mode else None,
              redoc_url='/redoc' if DEBUG_MODE.debug_mode else None,
              lifespan=lifespan)

app.include_router(healthcheck.router)
app.include_router(get_info.router.router)
app.include_router(broker_router)


async def main():
    await database.create_tables.create_tables()


if __name__ == '__main__':
    asyncio.run(main())
    uvicorn.run("main:app", host='0.0.0.0', port=7000, workers=WORKER_THREADS.count, reload=False)
