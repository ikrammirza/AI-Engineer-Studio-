from fastapi import APIRouter, Depends
from app.schemas.playground import PlaygroundRunRequest, PlaygroundRunResponse, ModelResult
from app.core.model_runner import run_models_parallel
from app.core.models_registry import list_models
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/playground", tags=["playground"])


@router.get("/models")
async def get_available_models(current_user: User = Depends(get_current_user)):
    return list_models()


@router.post("/run", response_model=PlaygroundRunResponse)
async def run_playground(
    payload: PlaygroundRunRequest,
    current_user: User = Depends(get_current_user),
):
    results = await run_models_parallel(
        model_keys=payload.model_keys,
        prompt=payload.prompt,
        system=payload.system,
    )

    total_cost = sum(r.cost_usd for r in results)

    return PlaygroundRunResponse(
        results=[ModelResult(**r.__dict__) for r in results],
        total_cost_usd=round(total_cost, 6),
        prompt=payload.prompt,
    )
