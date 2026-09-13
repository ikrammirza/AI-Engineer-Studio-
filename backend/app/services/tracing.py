import time

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Trace, TraceEvent


class TraceRecorder:
    def __init__(self, db: AsyncSession, trace: Trace):
        self.db = db
        self.trace = trace
        self._step_order = 0
        self._start_time = time.perf_counter()

    async def log_event(
        self,
        event_type: str,
        name: str,
        input_data: str,
        output_data: str,
        latency_ms: float | None = None,
    ) -> None:
        self._step_order += 1
        event = TraceEvent(
            trace_id=self.trace.id,
            step_order=self._step_order,
            event_type=event_type,
            name=name,
            input_data=input_data,
            output_data=output_data,
            latency_ms=latency_ms,
        )
        self.db.add(event)
        await self.db.commit()

    async def finish(self, output_summary: str, status: str = "success") -> None:
        self.trace.output_summary = output_summary
        self.trace.status = status
        self.trace.total_latency_ms = round((time.perf_counter() - self._start_time) * 1000, 2)
        await self.db.commit()


async def start_trace(db: AsyncSession, trace_type: str, input_summary: str) -> TraceRecorder:
    trace = Trace(trace_type=trace_type, input_summary=input_summary, status="running")
    db.add(trace)
    await db.flush()
    return TraceRecorder(db, trace)