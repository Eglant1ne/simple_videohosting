import asyncio
import aio_pika
import json

class RabbitMQClient:
    def __init__(self, config):
        self.config = config
        self.connection = None
        
    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.config.rabbitmq_url)
        self.channel = await self.connection.channel()
        
        await self.channel.declare_queue("convert_video_to_hls", durable=True)
    
    async def publish(self, queue: str, message: str):
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=queue
        )
    
    async def consume(self, queue: str, callback):
        queue_obj = await self.channel.declare_queue(queue, durable=True)
        
        async for message in queue_obj:
            async with message.process():
                success = await callback(json.loads(message.body.decode()))
                if not success:
                    await message.nack(requeue=True)
    
    async def close(self):
        if self.connection:
            await self.connection.close()
