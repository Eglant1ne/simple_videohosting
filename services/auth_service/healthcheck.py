from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

router: APIRouter = APIRouter()
"""
Роутер для health-check эндпоинтов.

Предоставляет endpoints для проверки работоспособности сервиса
и мониторинга состояния системы.

:var router: Экземпляр роутера FastAPI для health-check endpoints
:type router: APIRouter
"""


@router.get("/health", status_code=200, response_class=ORJSONResponse)
def health_check() -> ORJSONResponse:
    """
    Health-check эндпоинт для проверки работоспособности сервиса.

    Используется системами мониторинга, оркестрации (Docker) и
    балансировщиками нагрузки для проверки состояния сервиса.

    :return: JSON ответ с статусом здоровья сервиса
    :rtype: ORJSONResponse
    """
    return ORJSONResponse({"msg": "healthy"})
