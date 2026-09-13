from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models import Document, Chunk
from backend.app.services.chunking import chunk_text
from backend.app.services.embeddings import get_embedding, find_similar_chunks
from backend.app.services.llm import run_llm
from backend.app.services.extraction import extract_text, SUPPORTED_TYPES
from backend.app.services.tracing import start_trace
from backend.app.services.rag import answer_question
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])



class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    uploaded_at: datetime
    chunk_count: int


@router.post("", response_model=DocumentRead)
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    raw_bytes = await file.read()
    text = extract_text(raw_bytes, file.content_type)

    document = Document(
        filename=file.filename,
        content_type=file.content_type,
    )
    db.add(document)
    await db.flush()  # assigns document.id without ending the transaction

    pieces = chunk_text(text)

    for index, piece in enumerate(pieces):
        embedding = await get_embedding(piece)
        chunk = Chunk(
            document_id=document.id,
            chunk_index=index,
            content=piece,
            embedding=embedding,
        )
        db.add(chunk)

    await db.commit()
    await db.refresh(document)

    return DocumentRead(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        uploaded_at=document.uploaded_at,
        chunk_count=len(pieces),
    )

class ChunkResult(BaseModel):
    chunk_id: int
    document_id: int
    content: str
    similarity_score: float


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/search", response_model=list[ChunkResult])
async def search_chunks(
    data: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    query_embedding = await get_embedding(data.query)
    results = await find_similar_chunks(db, query_embedding, top_k=data.top_k)

    return [
        ChunkResult(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            similarity_score=round(1 - distance, 4),
        )
        for chunk, distance in results
    ]

RAG_PROMPT_TEMPLATE = """Answer the question using only the context below. If the context doesn't contain the answer, say you don't know.

Context:
{context}

Question: {question}

Answer:"""


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    model: str = "qwen2.5-coder:7b"


class AskResponse(BaseModel):
    answer: str
    model: str
    latency_ms: float
    retrieved_chunks: list[ChunkResult]


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    data: AskRequest,
    db: AsyncSession = Depends(get_db),
):
    recorder = await start_trace(db, trace_type="rag_query", input_summary=data.question)

    result = await answer_question(db, data.question, top_k=data.top_k, model=data.model)

    if result is None:
        await recorder.finish(output_summary="No documents found.", status="error")
        raise HTTPException(
            status_code=404,
            detail="No documents have been uploaded yet.",
        )

    chunk_results = [ChunkResult(**c) for c in result["retrieved_chunks"]]

    await recorder.log_event(
        event_type="retrieval",
        name="rag_search",
        input_data=data.question,
        output_data=f"{len(chunk_results)} chunks retrieved, top score: {chunk_results[0].similarity_score}",
    )

    await recorder.log_event(
        event_type="llm_call",
        name=result["model"],
        input_data=result["prompt"],
        output_data=result["answer"],
        latency_ms=result["latency_ms"],
    )

    await recorder.finish(output_summary=result["answer"])

    return AskResponse(
        answer=result["answer"],
        model=result["model"],
        latency_ms=result["latency_ms"],
        retrieved_chunks=chunk_results,
    )