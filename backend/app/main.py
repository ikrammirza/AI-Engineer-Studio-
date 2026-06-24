from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.auth import router as auth_router
from app.api.prompts import router as prompts_router
from app.api.playground import router as playground_router

app = FastAPI(
    title="AI Engineer Studio API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(prompts_router)
app.include_router(playground_router)


@app.get("/")
async def root():
    return {"message": "AI Engineer Studio API is running"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    db_ok = result.scalar() == 1
    return {
        "status": "ok" if db_ok else "error",
        "database": "connected" if db_ok else "unreachable",
    }
