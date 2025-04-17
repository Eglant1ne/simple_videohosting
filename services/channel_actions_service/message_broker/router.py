from faststream.rabbit.fastapi import RabbitRouter

from config import RABBITMQ_SETTINGS

rabbitmq_url = f'amqp://{RABBITMQ_SETTINGS.user}:{RABBITMQ_SETTINGS.password}@rabbitmq:5672/'
router = RabbitRouter(rabbitmq_url)
