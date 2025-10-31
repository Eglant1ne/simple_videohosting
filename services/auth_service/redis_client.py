import redis.asyncio as redis

from config import REDIS_SETTINGS

redis_client: redis.Redis = redis.Redis(password=REDIS_SETTINGS.password,
                                        port=6379,
                                        host='redis',
                                        decode_responses=True)
