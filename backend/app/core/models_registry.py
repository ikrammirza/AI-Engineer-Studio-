from dataclasses import dataclass


@dataclass
class ModelDefinition:
    id: str               # used in API calls
    name: str             # display name
    provider: str         # groq | openai | anthropic | google
    input_cost_per_1k: float   # $ per 1k input tokens
    output_cost_per_1k: float  # $ per 1k output tokens
    max_tokens: int


MODELS: dict[str, ModelDefinition] = {
    "groq/llama-3.3-70b": ModelDefinition(
        id="llama-3.3-70b-versatile",
        name="Llama 3.3 70B",
        provider="groq",
        input_cost_per_1k=0.00059,
        output_cost_per_1k=0.00079,
        max_tokens=8192,
    ),

    "groq/llama-3.1-8b": ModelDefinition(
        id="llama-3.1-8b-instant",
        name="Llama 3.1 8B",
        provider="groq",
        input_cost_per_1k=0.00005,
        output_cost_per_1k=0.00008,
        max_tokens=8192,
    ),

    "google/gemini-flash": ModelDefinition(
        id="gemini-2.5-flash",
        name="Gemini Flash",
        provider="google",
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        max_tokens=8192,
    ),

    "openai/gpt-4o-mini": ModelDefinition(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.00060,
        max_tokens=16384,
    ),

    "anthropic/claude-haiku": ModelDefinition(
        id="claude-haiku-4-5-20251001",
        name="Claude Haiku",
        provider="anthropic",
        input_cost_per_1k=0.00025,
        output_cost_per_1k=0.00125,
        max_tokens=8192,
    ),
}


def get_model(model_key: str) -> ModelDefinition | None:
    return MODELS.get(model_key)


def list_models() -> list[dict]:
    return [
        {
            "key": key,
            "name": m.name,
            "provider": m.provider,
            "max_tokens": m.max_tokens,
            "input_cost_per_1k": m.input_cost_per_1k,
            "output_cost_per_1k": m.output_cost_per_1k,
        }
        for key, m in MODELS.items()
    ]