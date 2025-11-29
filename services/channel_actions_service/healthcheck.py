from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

router: APIRouter = APIRouter()


@router.get("/health", status_code=200, response_class=ORJSONResponse)
def health_check() -> ORJSONResponse:
    """
    Эндпоинт для проверки здоровья сервиса.
    
    Используется для мониторинга работоспособности сервиса.
    Возвращает статус 200 и сообщение о здоровом состоянии.
    
    :return: JSON ответ с сообщением о статусе сервиса
    :rtype: ORJSONResponse
    """
    return ORJSONResponse({"msg": "healthy"})
