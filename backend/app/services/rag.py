from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.embeddings import get_embedding, find_similar_chunks
from backend.app.services.llm import run_llm
from backend.app.services.templates import render_template

DEFAULT_RAG_TEMPLATE = (
    "Answer the question using only the context below. "
    "If the context doesn't contain the answer, say you don't know.\n\n"
    "Context:\n{{context}}\n\nQuestion: {{question}}\n\nAnswer:"
)


async def answer_question(
    db: AsyncSession,
    question: str,
    top_k: int = 5,
    model: str = "qwen2.5-coder:7b",
    prompt_template: str | None = None,
) -> dict | None:
    query_embedding = await get_embedding(question)
    results = await find_similar_chunks(db, query_embedding, top_k=top_k)

    if not results:
        return None

    chunks = [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "content": chunk.content,
            "similarity_score": round(1 - distance, 4),
        }
        for chunk, distance in results
    ]

    context = "\n\n".join(c["content"] for c in chunks)
    template = prompt_template or DEFAULT_RAG_TEMPLATE
    prompt = render_template(template, {"context": context, "question": question})

    llm_result = await run_llm(prompt=prompt, model=model)

    return {
        "answer": llm_result.response,
        "model": llm_result.model,
        "latency_ms": llm_result.latency_ms,
        "prompt_tokens": llm_result.prompt_tokens,
        "completion_tokens": llm_result.completion_tokens,
        "retrieved_chunks": chunks,
        "prompt": prompt,
    }