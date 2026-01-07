import asyncio

import redis
import redis.asyncio as async_redis
import threading

from abc import ABC, abstractmethod
from typing import Optional


class AsyncCacheInterface(ABC):
    @abstractmethod
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None: ...

    @abstractmethod
    async def get(self, key: str) -> Optional[str]: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    async def set_if_not_exists(self, key: str, value: str, ttl: int) -> bool: ...


class SyncCacheInterface(ABC):
    @abstractmethod
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None: ...

    @abstractmethod
    def get(self, key: str) -> Optional[str]: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def set_if_not_exists(self, key: str, value: str, ttl: int) -> bool: ...


class SyncRedisCache(SyncCacheInterface):
    _instance: Optional['SyncRedisCache'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, redis_url: str):
        if self._initialized:
            return

        self._pool = redis.ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
            max_connections=20
        )
        self._redis = redis.Redis(connection_pool=self._pool)
        self._initialized = True

    def exists(self, key: str) -> bool:
        return bool(self._redis.exists(key))

    def set_if_not_exists(self, key: str, value: str, ttl: int) -> bool:
        return bool(self._redis.set(key, value, ex=ttl, nx=True))

    def get(self, key: str) -> str | None:
        return self._redis.get(key)

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self._redis.set(key, value, ex=ttl)

    def delete(self, key: str) -> None:
        self._redis.delete(key)


class AsyncRedisCache(AsyncCacheInterface):
    _instance: Optional['AsyncRedisCache'] = None
    _lock: Optional[asyncio.Lock] = None

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: Optional[async_redis.Redis] = None

    @classmethod
    async def get_instance(cls, redis_url: str) -> 'AsyncRedisCache':
        if cls._instance is None:
            if cls._lock is None:
                cls._lock = asyncio.Lock()

            async with cls._lock:
                if cls._instance is None:
                    instance = cls(redis_url)
                    instance._redis = async_redis.from_url(
                        redis_url,
                        decode_responses=True,
                        max_connections=20
                    )
                    cls._instance = instance
        return cls._instance

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        await self._redis.set(key, value, ex=ttl)

    async def get(self, key: str) -> Optional[str]:
        return await self._redis.get(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def set_if_not_exists(self, key: str, value: str, ttl: int) -> bool:
        result = await self._redis.set(key, value, ex=ttl, nx=True)
        return bool(result)

    async def close(self) -> None:
        await self._redis.aclose()
