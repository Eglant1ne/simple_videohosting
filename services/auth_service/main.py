import healthcheck

from fastapi import FastAPI

import database
from config import DEBUG_MODE

app = FastAPI(docs_url='/docs' if DEBUG_MODE.debug_mode else None,
              redoc_url='/redoc' if DEBUG_MODE.debug_mode else None)

app.include_router(healthcheck.router)


@app.on_event("startup")
async def startup_event():
    await database.create_tables.create_tables()
