from pydantic import BaseModel
import uuid
from datetime import datetime


class DatasetResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    row_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetDetailResponse(DatasetResponse):
    rows: list[dict]


class RunEvaluationRequest(BaseModel):
    dataset_id: uuid.UUID
    prompt_id: uuid.UUID
    model_key: str
    scoring_method: str = "llm"  # exact | contains | llm


class QuestionResult(BaseModel):
    question: str
    expected: str
    actual: str
    score: float
    passed: bool
    reasoning: str | None = None


class EvaluationRunResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    prompt_id: uuid.UUID | None
    model_key: str
    scoring_method: str
    status: str
    accuracy: float | None
    avg_score: float | None
    results: list[dict]
    prompt_version_number: int | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
