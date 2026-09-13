from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models import Dataset, Evaluation, EvaluationResult
from backend.app.services.rag import answer_question
from backend.app.services.evaluation import exact_match, semantic_similarity, determine_pass

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


class RunEvaluationRequest(BaseModel):
    dataset_id: int
    model: str = "qwen2.5-coder:7b"


class EvaluationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_item_id: int
    actual_answer: str
    exact_match: bool
    similarity_score: float
    passed: bool


class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    model: str
    status: str
    exact_match_score: float | None
    semantic_similarity_score: float | None
    passed_count: int
    failed_count: int


class EvaluationDetail(EvaluationRead):
    results: list[EvaluationResultRead]

class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    model: str
    status: str
    exact_match_score: float | None
    semantic_similarity_score: float | None
    avg_latency_ms: float | None
    passed_count: int
    failed_count: int

class EvaluationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_item_id: int
    actual_answer: str
    exact_match: bool
    similarity_score: float
    passed: bool
    latency_ms: float | None
    prompt_tokens: int | None
    completion_tokens: int | None

@router.post("/run", response_model=EvaluationRead)
async def run_evaluation(
    data: RunEvaluationRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.items))
        .where(Dataset.id == data.dataset_id)
    )
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.items:
        raise HTTPException(status_code=400, detail="Dataset has no items")

    from backend.app.services.evaluation import run_dataset_evaluation
    evaluation = await run_dataset_evaluation(db, dataset, data.model)
    return evaluation


@router.get("/{evaluation_id}", response_model=EvaluationDetail)
async def get_evaluation(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Evaluation)
        .options(selectinload(Evaluation.results))
        .where(Evaluation.id == evaluation_id)
    )
    evaluation = result.scalar_one_or_none()
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


@router.get("/{evaluation_id}/failures", response_model=list[EvaluationResultRead])
async def get_evaluation_failures(evaluation_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EvaluationResult).where(
            EvaluationResult.evaluation_id == evaluation_id,
            EvaluationResult.passed == False,  # noqa: E712
        )
    )
    return result.scalars().all()