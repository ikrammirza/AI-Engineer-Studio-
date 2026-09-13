import ast
import operator
from dataclasses import dataclass
from typing import Awaitable, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.embeddings import get_embedding, find_similar_chunks

from sqlalchemy import func, select

from backend.app.models import RefundRecord
@dataclass
class Tool:
    name: str
    description: str
    run: Callable[[str], Awaitable[str]]


TOOL_REGISTRY: dict[str, Tool] = {}


def register_tool(tool: Tool) -> None:
    TOOL_REGISTRY[tool.name] = tool


_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


async def calculator_tool(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return str(result)
    except Exception:
        return f"Error: could not evaluate '{expression}'"


register_tool(
    Tool(
        name="calculator",
        description="Evaluates a math expression like '42.50 * 3' or '(10 + 5) / 2'. Input must be a plain arithmetic expression.",
        run=calculator_tool,
    )
)

def make_rag_search_tool(db: AsyncSession) -> Tool:
    async def rag_search_tool(query: str) -> str:
        embedding = await get_embedding(query)
        results = await find_similar_chunks(db, embedding, top_k=3)

        if not results:
            return "No relevant documents found."

        return "\n\n".join(chunk.content for chunk, _distance in results)

    return Tool(
        name="rag_search",
        description="Searches uploaded documents for information relevant to a query. Input should be a plain-text search query.",
        run=rag_search_tool,
    )

ALLOWED_DB_OPERATIONS = {"count", "average", "sum", "list"}


def make_db_query_tool(db: AsyncSession) -> Tool:
    async def db_query_tool(operation: str) -> str:
        operation = operation.strip().lower()

        if operation not in ALLOWED_DB_OPERATIONS:
            return (
                f"Error: unsupported operation '{operation}'. "
                f"Allowed operations: {', '.join(ALLOWED_DB_OPERATIONS)}"
            )

        if operation == "count":
            result = await db.execute(select(func.count()).select_from(RefundRecord))
            return str(result.scalar())

        if operation == "average":
            result = await db.execute(select(func.avg(RefundRecord.amount)))
            avg = result.scalar()
            return str(round(avg, 2)) if avg is not None else "No records found."

        if operation == "sum":
            result = await db.execute(select(func.sum(RefundRecord.amount)))
            total = result.scalar()
            return str(round(total, 2)) if total is not None else "No records found."

        if operation == "list":
            result = await db.execute(select(RefundRecord))
            records = result.scalars().all()
            if not records:
                return "No records found."
            return "\n".join(f"{r.customer_name}: {r.amount}" for r in records)

    return Tool(
        name="db_query",
        description=(
            "Queries the refund_records database. Input must be exactly one of: "
            "'count' (number of refund records), 'average' (average refund amount), "
            "'sum' (total refund amount), or 'list' (list all records)."
        ),
        run=db_query_tool,
    )