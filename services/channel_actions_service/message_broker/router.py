from faststream.rabbit.fastapi import RabbitRouter

from config import RABBITMQ_SETTINGS

rabbitmq_url = f'amqp://{RABBITMQ_SETTINGS.user}:{RABBITMQ_SETTINGS.password}@rabbitmq:5672/'
"""
URL подключения к RabbitMQ брокеру сообщений.

Формируется из настроек подключения:
- Логин и пароль из RABBITMQ_SETTINGS
- Хост: rabbitmq (имя сервиса в Docker)
- Порт: 5672 (стандартный порт RabbitMQ)

Используется для установки соединения с брокером сообщений.
"""

router = RabbitRouter(rabbitmq_url)
"""
Роутер для работы с RabbitMQ через FastStream.

:param rabbitmq_url: URL для подключения к RabbitMQ брокеру

Обеспечивает интеграцию между FastAPI и RabbitMQ,
позволяя создавать подписчиков и издателей для обработки сообщений.
"""
