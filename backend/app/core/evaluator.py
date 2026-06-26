from app.core.model_runner import run_single_model


async def score_exact(actual: str, expected: str) -> dict:
    passed = actual.strip().lower() == expected.strip().lower()
    return {"score": 1.0 if passed else 0.0, "passed": passed, "reasoning": None}


async def score_contains(actual: str, expected: str) -> dict:
    passed = expected.strip().lower() in actual.strip().lower()
    return {"score": 1.0 if passed else 0.0, "passed": passed, "reasoning": None}


async def score_llm(question: str, expected: str, actual: str) -> dict:
    scoring_prompt = f"""You are an evaluation judge. Score this answer from 0.0 to 1.0.

Question: {question}
Expected answer: {expected}
Actual answer: {actual}

Rules:
- 1.0 = correct and complete
- 0.7 = mostly correct, minor issues
- 0.4 = partially correct
- 0.0 = wrong or irrelevant

Respond with ONLY a JSON object like this:
{{"score": 0.8, "reasoning": "The answer covers the main point but misses..."}}"""

    result = await run_single_model(
        model_key="groq/llama-3.1-8b",
        prompt=scoring_prompt,
        system="You are a precise evaluation judge. Always respond with valid JSON only.",
    )

    if result.error:
        return {"score": 0.0, "passed": False, "reasoning": f"Scoring error: {result.error}"}

    try:
        import json
        import re
        # Extract JSON from response
        match = re.search(r'\{.*\}', result.output, re.DOTALL)
        if match:
            data = json.loads(match.group())
            score = float(data.get("score", 0.0))
            return {
                "score": score,
                "passed": score >= 0.7,
                "reasoning": data.get("reasoning", ""),
            }
    except Exception:
        pass

    return {"score": 0.0, "passed": False, "reasoning": "Could not parse score"}


async def evaluate_single(
    question: str,
    expected: str,
    actual: str,
    scoring_method: str,
) -> dict:
    if scoring_method == "exact":
        scored = await score_exact(actual, expected)
    elif scoring_method == "contains":
        scored = await score_contains(actual, expected)
    else:
        scored = await score_llm(question, expected, actual)

    return {
        "question": question,
        "expected": expected,
        "actual": actual,
        **scored,
    }
