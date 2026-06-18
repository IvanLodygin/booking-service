import time
from typing import Callable

import redis
from fastapi import HTTPException, Request, status

from app.core.config import settings

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        
    return _redis_client


def _get_redis() -> Callable[[], redis.Redis]:
    return get_redis_client


async def rate_limit(request: Request) -> None:
    get_redis = request.app.state.get_redis if hasattr(request.app.state, "get_redis") else get_redis_client
    r = get_redis()

    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"
    now = int(time.time())
    window_start = now - settings.booking_rate_limit_window

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, settings.booking_rate_limit_window)
    results = pipe.execute()

    request_count = results[2]
    
    if request_count > settings.booking_rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down.",
        )
