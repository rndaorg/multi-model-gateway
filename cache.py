import redis.asyncio as redis
import hashlib
import json
from typing import Optional

redis_client = redis.Redis(host='localhost', port=6379, db=0)

class CacheManager:
    @staticmethod
    def _generate_hash(messages: list, model: str) -> str:
        content = json.dumps({"messages": messages, "model": model}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    async def get_cached_response(key: str) -> Optional[dict]:
        data = await redis_client.get(f"cache:{key}")
        return json.loads(data) if data else None

    @staticmethod
    async def set_cached_response(key: str, response: dict, ttl: int = 3600):
        await redis_client.setex(f"cache:{key}", ttl, json.dumps(response))

    @staticmethod
    async def check_rate_limit(api_key: str, limit: int) -> bool:
        key = f"ratelimit:{api_key}"
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, 60) # 1 minute window
        return current <= limit

    @staticmethod
    async def update_model_health(model: str, status: str):
        await redis_client.setex(f"health:{model}", 120, status) # 2 min TTL

    @staticmethod
    async def get_model_health(model: str) -> str:
        status = await redis_client.get(f"health:{model}")
        return status.decode() if status else "unknown"
