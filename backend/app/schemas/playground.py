from pydantic import BaseModel


class PlaygroundRunRequest(BaseModel):
    prompt: str
    system: str = ""
    model_keys: list[str]


class ModelResult(BaseModel):
    model_key: str
    model_name: str
    provider: str
    output: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    error: str | None = None


class PlaygroundRunResponse(BaseModel):
    results: list[ModelResult]
    total_cost_usd: float
    prompt: str
