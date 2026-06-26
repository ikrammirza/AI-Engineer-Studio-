import csv
import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.evaluation import EvaluationDataset, EvaluationRun
from app.models.prompt import Prompt, PromptVersion
from app.schemas.evaluation import (
    DatasetResponse, DatasetDetailResponse,
    RunEvaluationRequest, EvaluationRunResponse,
)
from app.core.deps import get_current_user
from app.core.model_runner import run_single_model
from app.core.evaluator import evaluate_single
from app.core.interpolation import interpolate
from app.models.user import User

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/datasets", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    name: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    rows = []
    for row in reader:
        # Support flexible column names
        question = row.get("question") or row.get("input") or row.get("prompt") or ""
        expected = row.get("expected") or row.get("expected_answer") or row.get("answer") or row.get("output") or ""
        if question and expected:
            rows.append({"question": question.strip(), "expected": expected.strip()})

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="CSV must have 'question' and 'expected' columns"
        )

    dataset = EvaluationDataset(
        name=name,
        description=description or None,
        owner_id=current_user.id,
        rows=rows,
        row_count=len(rows),
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=list[DatasetResponse])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EvaluationDataset)
        .where(EvaluationDataset.owner_id == current_user.id)
        .order_by(EvaluationDataset.created_at.desc())
    )
    return result.scalars().all()


@router.get("/datasets/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EvaluationDataset).where(
            EvaluationDataset.id == dataset_id,
            EvaluationDataset.owner_id == current_user.id,
        )
    )
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/runs", response_model=EvaluationRunResponse, status_code=201)
async def run_evaluation(
    payload: RunEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get dataset
    ds_result = await db.execute(
        select(EvaluationDataset).where(
            EvaluationDataset.id == payload.dataset_id,
            EvaluationDataset.owner_id == current_user.id,
        )
    )
    dataset = ds_result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get latest prompt version
    pv_result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == payload.prompt_id)
        .order_by(PromptVersion.version_number.desc())
        .limit(1)
    )
    prompt_version = pv_result.scalar_one_or_none()
    if not prompt_version:
        raise HTTPException(status_code=404, detail="Prompt has no versions")

    # Create run record
    run = EvaluationRun(
        dataset_id=dataset.id,
        prompt_id=payload.prompt_id,
        owner_id=current_user.id,
        model_key=payload.model_key,
        scoring_method=payload.scoring_method,
        status="running",
        prompt_version_number=prompt_version.version_number,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Run evaluation
    results = []
    for row in dataset.rows:
        question = row["question"]
        expected = row["expected"]

        # Interpolate question into prompt template
        interpolated = interpolate(prompt_version.content, {"question": question, "input": question})
        final_prompt = interpolated["result"]

        # Run model
        model_result = await run_single_model(
            model_key=payload.model_key,
            prompt=final_prompt,
        )

        actual = model_result.output if not model_result.error else ""

        # Score
        scored = await evaluate_single(
            question=question,
            expected=expected,
            actual=actual,
            scoring_method=payload.scoring_method,
        )
        results.append(scored)

    # Calculate metrics
    scores = [r["score"] for r in results]
    passed = [r["passed"] for r in results]
    accuracy = sum(passed) / len(passed) if passed else 0.0
    avg_score = sum(scores) / len(scores) if scores else 0.0

    # Update run
    run.results = results
    run.accuracy = round(accuracy, 4)
    run.avg_score = round(avg_score, 4)
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(run)
    return run


@router.get("/runs", response_model=list[EvaluationRunResponse])
async def list_runs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EvaluationRun)
        .where(EvaluationRun.owner_id == current_user.id)
        .order_by(EvaluationRun.created_at.desc())
    )
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id,
            EvaluationRun.owner_id == current_user.id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
