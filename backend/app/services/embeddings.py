import httpx

from backend.app.config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Chunk
EMBEDDING_MODEL = "nomic-embed-text"


async def get_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.ollama_url}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]

async def find_similar_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[tuple[Chunk, float]]:
    result = await db.execute(
        select(Chunk, Chunk.embedding.cosine_distance(query_embedding).label("distance"))
        .order_by("distance")
        .limit(top_k)
    )
    return [(row.Chunk, row.distance) for row in result]