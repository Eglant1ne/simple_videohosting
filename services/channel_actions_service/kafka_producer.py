import asyncio
from aiokafka import AIOKafkaProducer

producer: AIOKafkaProducer = None


def create_producer():
    global producer
    loop = asyncio.get_running_loop()
    producer = AIOKafkaProducer(bootstrap_servers='kafka:9092', enable_idempotence=True, loop=loop)
    return producer
