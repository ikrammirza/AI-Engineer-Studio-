from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models import Prompt, PromptVersion
from backend.app.schemas import (
    PromptCreate,
    PromptRead,
    PromptVersionCreate,
    PromptVersionRead,
    PromptTestRequest,
    PromptTestResponse,
)
from backend.app.services.templates import render_template
from backend.app.services.llm import generate_response

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


@router.post("", response_model=PromptRead)
async def create_prompt(
    data: PromptCreate,
    db: AsyncSession = Depends(get_db),
):
    prompt = Prompt(name=data.name)
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    return prompt


@router.get("", response_model=list[PromptRead])
async def list_prompts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Prompt))
    return result.scalars().all()


@router.get("/{prompt_id}", response_model=PromptRead)
async def get_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    prompt = await db.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    prompt = await db.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    await db.delete(prompt)
    await db.commit()

@router.post("/{prompt_id}/versions", response_model=PromptVersionRead)
async def create_prompt_version(
    prompt_id: int,
    data: PromptVersionCreate,
    db: AsyncSession = Depends(get_db),
):
    prompt = await db.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    result = await db.execute(
        select(func.max(PromptVersion.version_number)).where(
            PromptVersion.prompt_id == prompt_id
        )
    )
    current_max = result.scalar()
    next_version = (current_max or 0) + 1

    version = PromptVersion(
        prompt_id=prompt_id,
        version_number=next_version,
        content=data.content,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionRead])
async def list_prompt_versions(prompt_id: int, db: AsyncSession = Depends(get_db)):
    prompt = await db.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version_number)
    )
    return result.scalars().all()


@router.get("/{prompt_id}/versions/{version_id}", response_model=PromptVersionRead)
async def get_prompt_version(
    prompt_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
):
    version = await db.get(PromptVersion, version_id)
    if version is None or version.prompt_id != prompt_id:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    return version

@router.post(
    "/{prompt_id}/versions/{version_id}/test",
    response_model=PromptTestResponse,
)
async def test_prompt_version(
    prompt_id: int,
    version_id: int,
    data: PromptTestRequest,
    db: AsyncSession = Depends(get_db),
):
    version = await db.get(PromptVersion, version_id)
    if version is None or version.prompt_id != prompt_id:
        raise HTTPException(status_code=404, detail="Prompt version not found")

    try:
        rendered = render_template(version.content, data.variables)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    llm_response = await generate_response(prompt=rendered, model=data.model)

    return PromptTestResponse(
        rendered_prompt=rendered,
        response=llm_response,
        model=data.model,
    )