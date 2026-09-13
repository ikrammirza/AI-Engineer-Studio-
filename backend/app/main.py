from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.database import Base, engine
from backend.app.logging_config import setup_logging
from backend.app.routers import prompts
from backend.app.services.llm import generate_response
from backend.app import models  # noqa: F401 (registers models for table creation)
from backend.app.routers import prompts, models, documents
from backend.app.routers import prompts, models, documents, agent, traces, datasets, evaluations, experiments
# Initialize logging before anything else
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Create database tables if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Application handles incoming requests here

    # SHUTDOWN: Close all pooled database connections cleanly
    await engine.dispose()


app = FastAPI(
    title="AI Engineer Studio",
    version="0.1.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    prompt: str
    model: str = settings.default_model


@app.get("/")
async def root():
    return {"message": "AI Engineer Studio API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    response = await generate_response(
        prompt=request.prompt,
        model=request.model,
    )
    return {
        "response": response,
        "model": request.model,
    }


app.include_router(prompts.router)
app.include_router(models.router)
app.include_router(documents.router)
app.include_router(agent.router)
app.include_router(traces.router)
app.include_router(datasets.router)
app.include_router(evaluations.router)
app.include_router(experiments.router)