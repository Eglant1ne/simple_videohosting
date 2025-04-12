from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

router = APIRouter()


@router.get("/health", status_code=200, response_class=ORJSONResponse)
def health_check():
    return ORJSONResponse({"msg": "healthy"})
