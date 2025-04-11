import healthcheck
from fastapi import FastAPI

app = FastAPI()

app.include_router(healthcheck.router)
