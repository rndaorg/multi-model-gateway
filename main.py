from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from gateway import router
import uvicorn

app = FastAPI(title="Multi-Model API Gateway")

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    strategy: str = "performance" # Options: performance, cost, balanced

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    try:
        result = await router.route_request(request.messages, request.strategy)
        return {
            "id": "gateway-123",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": result["response"]},
                "finish_reason": "stop"
            }],
            "usage": {
                "total_tokens": result["metadata"]["tokens"],
                "estimated_cost_usd": result["metadata"]["cost"]
            },
            "gateway_metadata": {
                "model_used": result["metadata"]["model"],
                "latency_s": result["metadata"]["latency"],
                "strategy": request.strategy
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/usage/stats")
async def get_stats():
    return {"total_requests": len(router.usage_log), "logs": router.usage_log}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
