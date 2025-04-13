from contextlib import asynccontextmanager
from fastapi import FastAPI

import healthcheck
from auth import router

import database
from config import DEBUG_MODE

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    await database.create_tables.create_tables()
    yield
    print("clean up lifespan")


app = FastAPI(docs_url='/docs' if DEBUG_MODE.debug_mode else None,
              redoc_url='/redoc' if DEBUG_MODE.debug_mode else None,
              lifespan=app_lifespan)

app.include_router(healthcheck.router)
app.include_router(router.router)
