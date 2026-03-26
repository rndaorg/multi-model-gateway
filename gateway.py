import os
import time
import json
from typing import List, Dict, Optional
from litellm import completion, ModelResponse
from litellm.exceptions import APIError, RateLimitError, Timeout

# Model Configuration with Pricing (per 1k tokens)
MODEL_CONFIG = {
    "gpt-4o": {"provider": "openai", "input_cost": 0.005, "output_cost": 0.015, "priority": 1},
    "gpt-3.5-turbo": {"provider": "openai", "input_cost": 0.0005, "output_cost": 0.0015, "priority": 2},
    "claude-3-haiku": {"provider": "anthropic", "input_cost": 0.00025, "output_cost": 0.00125, "priority": 3},
    "ollama/llama3": {"provider": "ollama", "input_cost": 0.0, "output_cost": 0.0, "priority": 4}, # Local
}

class GatewayRouter:
    def __init__(self):
        self.usage_log = []

    def get_strategy_models(self, strategy: str) -> List[str]:
        """Returns ordered list of models based on strategy"""
        if strategy == "cost":
            # Sort by total estimated cost (input + output avg)
            sorted_models = sorted(MODEL_CONFIG.items(), key=lambda x: x[1]['input_cost'] + x[1]['output_cost'])
            return [m[0] for m in sorted_models]
        elif strategy == "performance":
            # Sort by priority (assumed performance tier)
            sorted_models = sorted(MODEL_CONFIG.items(), key=lambda x: x[1]['priority'])
            return [m[0] for m in sorted_models]
        else:
            return list(MODEL_CONFIG.keys())

    def calculate_cost(self, model: str, usage: Dict) -> float:
        config = MODEL_CONFIG.get(model, {"input_cost": 0, "output_cost": 0})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        cost = (prompt_tokens / 1000 * config['input_cost']) + \
               (completion_tokens / 1000 * config['output_cost'])
        return round(cost, 6)

    async def route_request(self, messages: List[Dict], strategy: str = "performance"):
        candidate_models = self.get_strategy_models(strategy)
        last_error = None
        
        for model in candidate_models:
            try:
                start_time = time.time()
                
                # LiteLLM normalizes the call across providers
                response: ModelResponse = completion(
                    model=model,
                    messages=messages,
                    stream=False
                )
                
                latency = time.time() - start_time
                cost = self.calculate_cost(model, response.usage)
                
                # Log usage
                log_entry = {
                    "model": model,
                    "latency": round(latency, 3),
                    "cost": cost,
                    "tokens": response.usage['total_tokens'],
                    "status": "success"
                }
                self.usage_log.append(log_entry)
                
                return {
                    "response": response.choices[0].message.content,
                    "metadata": log_entry
                }

            except (APIError, RateLimitError, Timeout) as e:
                last_error = e
                print(f"⚠️ {model} failed: {str(e)}. Falling back to next model...")
                continue
        
        raise Exception(f"All models failed. Last error: {str(last_error)}")

router = GatewayRouter()
