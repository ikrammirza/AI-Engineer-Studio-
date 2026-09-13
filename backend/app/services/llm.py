import logging
import time

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from backend.app.config import settings

logger = logging.getLogger(__name__)


class LLMResult(BaseModel):
    response: str
    model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int


async def run_llm(prompt: str, model: str = settings.default_model) -> LLMResult:
    start = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()

    except httpx.TimeoutException:
        logger.error("Ollama request timed out for model %s", model)
        raise HTTPException(
            status_code=504,
            detail="The request to Ollama timed out. The model may be slow or overloaded.",
        )
    
    except httpx.ConnectError:
        logger.error("Could not connect to Ollama at %s", settings.ollama_url)
        raise HTTPException(
            status_code=503,
            detail="Could not reach the Ollama server. Is it running?",
        )

    except httpx.HTTPStatusError as exc:
        logger.error("Ollama returned an error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned an error: {exc.response.text}",
        )

    latency_ms = (time.perf_counter() - start) * 1000

    return LLMResult(
        response=data["response"],
        model=model,
        latency_ms=round(latency_ms, 2),
        prompt_tokens=data.get("prompt_eval_count", 0),
        completion_tokens=data.get("eval_count", 0),
    )


async def generate_response(prompt: str, model: str = settings.default_model) -> str:
    result = await run_llm(prompt, model)
    return result.response