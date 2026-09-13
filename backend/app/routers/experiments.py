from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models import Dataset, Experiment, ExperimentVariant
from backend.app.services.evaluation import run_dataset_evaluation

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


class VariantConfig(BaseModel):
    label: str
    model: str
    prompt_template: str | None = None


class CreateExperimentRequest(BaseModel):
    name: str
    dataset_id: int
    variants: list[VariantConfig]


class VariantResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    model: str
    exact_match_score: float | None = None
    semantic_similarity_score: float | None = None
    avg_latency_ms: float | None = None
    passed_count: int | None = None
    failed_count: int | None = None


class ExperimentResult(BaseModel):
    id: int
    name: str
    dataset_id: int
    variants: list[VariantResult]


@router.post("/run", response_model=ExperimentResult)
async def run_experiment(
    data: CreateExperimentRequest,
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

    experiment = Experiment(name=data.name, dataset_id=dataset.id)
    db.add(experiment)
    await db.flush()

    variant_results = []

    for variant_config in data.variants:
        evaluation = await run_dataset_evaluation(
            db,
            dataset,
            model=variant_config.model,
            prompt_template=variant_config.prompt_template,
        )

        variant = ExperimentVariant(
            experiment_id=experiment.id,
            label=variant_config.label,
            model=variant_config.model,
            prompt_template=variant_config.prompt_template,
            evaluation_id=evaluation.id,
        )
        db.add(variant)

        variant_results.append(
            VariantResult(
                label=variant_config.label,
                model=variant_config.model,
                exact_match_score=evaluation.exact_match_score,
                semantic_similarity_score=evaluation.semantic_similarity_score,
                avg_latency_ms=evaluation.avg_latency_ms,
                passed_count=evaluation.passed_count,
                failed_count=evaluation.failed_count,
            )
        )

    await db.commit()

    return ExperimentResult(
        id=experiment.id,
        name=experiment.name,
        dataset_id=experiment.dataset_id,
        variants=variant_results,
    )