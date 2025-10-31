import asyncio
import uvicorn
import healthcheck
import database

from fastapi import FastAPI

from auth import router as auth_router

from config import DEBUG_MODE, WORKER_THREADS

app = FastAPI(docs_url='/docs' if DEBUG_MODE.debug_mode else None,
              redoc_url='/redoc' if DEBUG_MODE.debug_mode else None)

app.include_router(healthcheck.router)
app.include_router(auth_router.router)


async def main():
    await database.create_tables.create_tables()


if __name__ == '__main__':
    asyncio.run(main())
    uvicorn.run("main:app", host='0.0.0.0', port=8000, workers=WORKER_THREADS.count, reload=False)
