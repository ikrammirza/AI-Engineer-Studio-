from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.services.agent import run_agent
from backend.app.services.tools import TOOL_REGISTRY, make_rag_search_tool, make_db_query_tool
from backend.app.services.tracing import start_trace

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class AgentRequest(BaseModel):
    task: str
    model: str = "qwen2.5-coder:7b"


class AgentResponse(BaseModel):
    answer: str
    steps: list[dict]
    trace_id: int


@router.post("/run", response_model=AgentResponse)
async def run_agent_endpoint(
    data: AgentRequest,
    db: AsyncSession = Depends(get_db),
):
    tools = dict(TOOL_REGISTRY)
    tools["rag_search"] = make_rag_search_tool(db)
    tools["db_query"] = make_db_query_tool(db)

    recorder = await start_trace(db, trace_type="agent_run", input_summary=data.task)

    async def on_step(event_type, name, input_data, output_data, latency_ms):
        await recorder.log_event(event_type, name, str(input_data), str(output_data), latency_ms)

    result = await run_agent(
        task=data.task,
        tools=tools,
        model=data.model,
        on_step=on_step,
    )

    await recorder.finish(output_summary=result["answer"])

    return AgentResponse(answer=result["answer"], steps=result["steps"], trace_id=recorder.trace.id)