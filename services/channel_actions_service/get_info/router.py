from fastapi import APIRouter

router = APIRouter(prefix='/channel_actions', tags=['get_info'])
"""
Роутер для обработки запросов связанных с действиями каналов.

:param prefix: Базовый префикс для всех эндпоинтов роутера
:type prefix: str
:param tags: Группировка эндпоинтов в документации Swagger
:type tags: List[str]

Все эндпоинты этого роутера будут иметь префикс '/channel_actions'
и отображаться в группе 'get_info' в автоматической документации.
"""
