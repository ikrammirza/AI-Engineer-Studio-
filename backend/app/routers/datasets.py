import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models import Dataset, DatasetItem

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


class DatasetItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    expected_answer: str


class DatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    item_count: int


class DatasetDetail(DatasetRead):
    items: list[DatasetItemRead]


@router.post("", response_model=DatasetRead)
async def upload_dataset(
    name: str,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    raw_bytes = await file.read()
    text = raw_bytes.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text))
    required_columns = {"question", "expected_answer"}
    if not required_columns.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have columns: {', '.join(required_columns)}. "
            f"Found: {reader.fieldnames}",
        )

    dataset = Dataset(name=name)
    db.add(dataset)
    await db.flush()

    item_count = 0
    for row in reader:
        db.add(
            DatasetItem(
                dataset_id=dataset.id,
                question=row["question"],
                expected_answer=row["expected_answer"],
            )
        )
        item_count += 1

    if item_count == 0:
        raise HTTPException(status_code=400, detail="CSV file contains no data rows.")

    await db.commit()
    await db.refresh(dataset)

    return DatasetRead(
        id=dataset.id,
        name=dataset.name,
        created_at=dataset.created_at,
        item_count=item_count,
    )


@router.get("", response_model=list[DatasetRead])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Dataset).options(selectinload(Dataset.items))
    )
    datasets = result.scalars().all()
    return [
        DatasetRead(
            id=d.id, name=d.name, created_at=d.created_at, item_count=len(d.items)
        )
        for d in datasets
    ]


@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Dataset)
        .options(selectinload(Dataset.items))
        .where(Dataset.id == dataset_id)
    )
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return DatasetDetail(
        id=dataset.id,
        name=dataset.name,
        created_at=dataset.created_at,
        item_count=len(dataset.items),
        items=dataset.items,
    )