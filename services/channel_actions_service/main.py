import asyncio
import uvicorn

import healthcheck
import get_info
import database

from contextlib import asynccontextmanager

from fastapi import FastAPI

from kafka_producer import create_producer

from config import DEBUG_MODE, WORKER_THREADS


@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = await create_producer()
    await producer.start()
    yield
    await producer.stop()


app = FastAPI(docs_url='/docs' if DEBUG_MODE.debug_mode else None,
              redoc_url='/redoc' if DEBUG_MODE.debug_mode else None,
              lifespan=lifespan)

app.include_router(healthcheck.router)
app.include_router(get_info.router.router)


async def main():
    await database.create_tables.create_tables()


if __name__ == '__main__':
    asyncio.run(main())
    uvicorn.run("main:app", host='0.0.0.0', port=7000, workers=WORKER_THREADS.count, reload=False)
