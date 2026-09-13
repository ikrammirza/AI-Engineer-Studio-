import asyncio
import httpx

from backend.app.config import settings
from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.llm import run_llm, LLMResult


router = APIRouter(prefix="/api/v1/models", tags=["models"])


class CompareRequest(BaseModel):
    prompt: str
    models: list[str]


@router.post("/compare", response_model=list[LLMResult])
async def compare_models(data: CompareRequest):
    tasks = [run_llm(prompt=data.prompt, model=model) for model in data.models]
    results = await asyncio.gather(*tasks)
    return results

@router.get("/registry")
async def list_available_models():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.ollama_url}/api/tags")
        response.raise_for_status()
        data = response.json()

    return [
        {"name": m["name"], "size_bytes": m["size"]}
        for m in data.get("models", [])
    ]

