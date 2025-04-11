import healthcheck

from fastapi import FastAPI

from database.create_tables import create_tables
from config import DEBUG_MODE

app = FastAPI(docs_url='/docs' if DEBUG_MODE.debug_mode else None,
              redoc_url='/redoc' if DEBUG_MODE.debug_mode else None)

app.include_router(healthcheck.router)


@app.on_event("startup")
async def startup_event():
    await create_tables()
