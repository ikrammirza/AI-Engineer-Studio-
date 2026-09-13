from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models import Trace

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])


class TraceEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_order: int
    event_type: str
    name: str
    input_data: str | None
    output_data: str | None
    latency_ms: float | None


class TraceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trace_type: str
    input_summary: str
    status: str
    total_latency_ms: float | None
    created_at: datetime


class TraceDetail(TraceListItem):
    output_summary: str | None
    events: list[TraceEventRead]


@router.get("", response_model=list[TraceListItem])
async def list_traces(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trace).order_by(Trace.id.desc()))
    return result.scalars().all()


@router.get("/{trace_id}", response_model=TraceDetail)
async def get_trace(trace_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Trace)
        .options(selectinload(Trace.events))
        .where(Trace.id == trace_id)
    )
    trace = result.scalar_one_or_none()

    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")

    return trace