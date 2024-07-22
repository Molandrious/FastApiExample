from typing import TYPE_CHECKING

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from loguru import logger
from redis import asyncio as asyncio_redis

from settings import Settings

if TYPE_CHECKING:
    from redis.asyncio.client import Redis


class RedisClient:
    def __init__(self):
        self._client: Redis = asyncio_redis.from_url(
            url=Settings().env.redis_dsn.unicode_string(),
            encoding='utf8',
            decode_responses=True,
        )

    def init_cache(self) -> None:
        FastAPICache.init(
            backend=RedisBackend(self._client),
        )

    async def check_connection(self) -> None:
        if not await self._client.ping():
            logger.warning('Redis connection failed')
        else:
            logger.trace('Redis connection established')

    async def close(self):
        await self._client.close()
