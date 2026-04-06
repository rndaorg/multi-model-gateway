from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
from database import init_db, get_db, AsyncSessionLocal
from models import APIKey
from cache import CacheManager
from services import route_and_stream, health_check_loop
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start Health Check Background Task
    task = asyncio.create_task(health_check_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

# Dependency: Validate API Key
async def verify_api_key(x_api_key: str = Header(...)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(APIKey).where(APIKey.key == x_api_key))
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        
        # Rate Limit Check
        if not await CacheManager.check_rate_limit(api_key.key, api_key.rate_limit):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
        return api_key.id

@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    api_key_id: int = Depends(verify_api_key)
):
    body = await request.json()
    messages = body.get("messages", [])
    strategy = body.get("strategy", "performance")
    stream = body.get("stream", False)

    # 1. Check Cache (Only for non-streaming)
    if not stream:
        cache_key = CacheManager._generate_hash(messages, strategy)
        cached = await CacheManager.get_cached_response(cache_key)
        if cached:
            return cached

    # 2. Route & Stream
    if stream:
        return StreamingResponse(
            route_and_stream(messages, strategy, api_key_id),
            media_type="text/event-stream"
        )
    else:
        # Non-streaming wrapper for simplicity in this snippet
        # In production, you'd duplicate logic to collect stream then return JSON
        raise HTTPException(status_code=400, detail="Streaming is recommended for this gateway. Set stream=true.")

@app.get("/health/models")
async def get_model_health():
    health = {}
    for model in ["gpt-4o", "gpt-3.5-turbo", "ollama/llama3"]:
        health[model] = await CacheManager.get_model_health(model)
    return health

# Seed an API Key on startup (Simplified)
import sqlite3
def seed_data():
    # This is a hack for the demo to ensure an API key exists
    # In prod, use an admin endpoint
    pass
