import time
import asyncio
from dataclasses import dataclass
from app.core.models_registry import get_model, ModelDefinition
from app.core.config import settings


@dataclass
class RunResult:
    model_key: str
    model_name: str
    provider: str
    output: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    error: str | None = None


def _calculate_cost(model: ModelDefinition, input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1000) * model.input_cost_per_1k
    output_cost = (output_tokens / 1000) * model.output_cost_per_1k
    return round(input_cost + output_cost, 6)


async def run_groq(model: ModelDefinition, prompt: str, system: str) -> tuple[str, int, int]:
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    messages = []

    if system:
        messages.append({"role": "system", "content": system})

    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=model.id,
        messages=messages,
        max_tokens=1024,
    )

    content = response.choices[0].message.content or ""

    return (
        content,
        response.usage.prompt_tokens,
        response.usage.completion_tokens,
    )


async def run_openai(model: ModelDefinition, prompt: str, system: str) -> tuple[str, int, int]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    messages = []

    if system:
        messages.append({"role": "system", "content": system})

    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=model.id,
        messages=messages,
        max_tokens=1024,
    )

    content = response.choices[0].message.content or ""

    return (
        content,
        response.usage.prompt_tokens,
        response.usage.completion_tokens,
    )


async def run_anthropic(model: ModelDefinition, prompt: str, system: str) -> tuple[str, int, int]:
    import anthropic

    client = anthropic.AsyncAnthropic(
        api_key=settings.ANTHROPIC_API_KEY
    )

    response = await client.messages.create(
        model=model.id,
        max_tokens=1024,
        system=system or "You are a helpful assistant.",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    content = response.content[0].text

    return (
        content,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )


async def run_google(model: ModelDefinition, prompt: str, system: str) -> tuple[str, int, int]:
    import google.generativeai as genai

    genai.configure(
        api_key=settings.GOOGLE_API_KEY
    )

    gemini = genai.GenerativeModel(
        model_name=model.id,
        system_instruction=system if system else None,
    )

    response = await gemini.generate_content_async(
        prompt
    )

    content = response.text or ""

    input_tokens = 0
    output_tokens = 0

    if hasattr(response, "usage_metadata"):
        input_tokens = getattr(
            response.usage_metadata,
            "prompt_token_count",
            0
        )

        output_tokens = getattr(
            response.usage_metadata,
            "candidates_token_count",
            0
        )

    return content, input_tokens, output_tokens


async def run_single_model(
    model_key: str,
    prompt: str,
    system: str = ""
) -> RunResult:

    model = get_model(model_key)

    if not model:
        return RunResult(
            model_key=model_key,
            model_name=model_key,
            provider="unknown",
            output="",
            input_tokens=0,
            output_tokens=0,
            cost_usd=0,
            latency_ms=0,
            error=f"Unknown model: {model_key}",
        )

    start = time.monotonic()

    try:

        if model.provider == "groq":

            output, input_tokens, output_tokens = await run_groq(
                model,
                prompt,
                system
            )

        elif model.provider == "openai":

            output, input_tokens, output_tokens = await run_openai(
                model,
                prompt,
                system
            )

        elif model.provider == "anthropic":

            output, input_tokens, output_tokens = await run_anthropic(
                model,
                prompt,
                system
            )

        elif model.provider == "google":

            output, input_tokens, output_tokens = await run_google(
                model,
                prompt,
                system
            )

        else:

            raise ValueError(
                f"Unsupported provider: {model.provider}"
            )


        latency_ms = int(
            (time.monotonic() - start) * 1000
        )

        cost = _calculate_cost(
            model,
            input_tokens,
            output_tokens
        )


        return RunResult(
            model_key=model_key,
            model_name=model.name,
            provider=model.provider,
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
        )


    except Exception as e:

        latency_ms = int(
            (time.monotonic() - start) * 1000
        )

        return RunResult(
            model_key=model_key,
            model_name=model.name,
            provider=model.provider,
            output="",
            input_tokens=0,
            output_tokens=0,
            cost_usd=0,
            latency_ms=latency_ms,
            error=str(e),
        )


async def run_models_parallel(
    model_keys: list[str],
    prompt: str,
    system: str = ""
) -> list[RunResult]:

    tasks = [
        run_single_model(
            key,
            prompt,
            system
        )
        for key in model_keys
    ]

    return await asyncio.gather(*tasks)