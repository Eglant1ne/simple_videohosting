import healthcheck

from fastapi import FastAPI

from database.create_tables import create_tables

app = FastAPI()

app.include_router(healthcheck.router)


@app.on_event("startup")
async def startup_event():
    await create_tables()
