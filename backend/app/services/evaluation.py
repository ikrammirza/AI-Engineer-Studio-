from backend.app.services.embeddings import get_embedding
from backend.app.models import Dataset, Evaluation, EvaluationResult
from backend.app.services.rag import answer_question
SIMILARITY_PASS_THRESHOLD = 0.75


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def exact_match(expected: str, actual: str) -> bool:
    return _normalize(expected) == _normalize(actual)


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = sum(a * a for a in vec_a) ** 0.5
    magnitude_b = sum(b * b for b in vec_b) ** 0.5
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)


async def semantic_similarity(expected: str, actual: str) -> float:
    expected_embedding = await get_embedding(expected)
    actual_embedding = await get_embedding(actual)
    similarity = _cosine_similarity(expected_embedding, actual_embedding)
    return round(similarity, 4)


def determine_pass(is_exact_match: bool, similarity: float) -> bool:
    return is_exact_match or similarity >= SIMILARITY_PASS_THRESHOLD

async def run_dataset_evaluation(
    db,
    dataset: Dataset,
    model: str,
    prompt_template: str | None = None,
) -> Evaluation:
    evaluation = Evaluation(dataset_id=dataset.id, model=model, status="running")
    db.add(evaluation)
    await db.flush()

    exact_match_hits = 0
    similarity_sum = 0.0
    latency_sum = 0.0
    passed_count = 0
    failed_count = 0

    for item in dataset.items:
        rag_result = await answer_question(
            db, item.question, model=model, prompt_template=prompt_template
        )
        actual_answer = rag_result["answer"] if rag_result else ""
        latency = rag_result["latency_ms"] if rag_result else 0.0

        is_exact = exact_match(item.expected_answer, actual_answer)
        similarity = await semantic_similarity(item.expected_answer, actual_answer)
        passed = determine_pass(is_exact, similarity)

        exact_match_hits += int(is_exact)
        similarity_sum += similarity
        latency_sum += latency
        passed_count += int(passed)
        failed_count += int(not passed)

        db.add(
            EvaluationResult(
                evaluation_id=evaluation.id,
                dataset_item_id=item.id,
                actual_answer=actual_answer,
                exact_match=is_exact,
                similarity_score=similarity,
                passed=passed,
                latency_ms=latency,
                prompt_tokens=rag_result["prompt_tokens"] if rag_result else None,
                completion_tokens=rag_result["completion_tokens"] if rag_result else None,
            )
        )

    item_count = len(dataset.items)
    evaluation.exact_match_score = round(exact_match_hits / item_count, 4)
    evaluation.semantic_similarity_score = round(similarity_sum / item_count, 4)
    evaluation.avg_latency_ms = round(latency_sum / item_count, 2)
    evaluation.passed_count = passed_count
    evaluation.failed_count = failed_count
    evaluation.status = "success"

    await db.commit()
    await db.refresh(evaluation)
    return evaluation