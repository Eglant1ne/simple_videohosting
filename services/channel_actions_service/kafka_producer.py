import asyncio
from aiokafka import AIOKafkaProducer

kafka_producer = None


async def create_producer():
    global kafka_producer
    loop = asyncio.get_running_loop()
    kafka_producer = AIOKafkaProducer(bootstrap_servers='kafka:9092', enable_idempotence=True, loop=loop)
    return kafka_producer
