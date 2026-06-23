from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.models.prompt import Prompt, PromptVersion
from app.models.user import User
from app.schemas.prompt import (
    PromptCreate, PromptUpdate, PromptSaveVersion,
    PromptResponse, PromptVersionResponse,
    InterpolateRequest, InterpolateResponse,
)
from app.core.deps import get_current_user
from app.core.interpolation import extract_variables, interpolate
import uuid

router = APIRouter(prefix="/prompts", tags=["prompts"])


async def _get_prompt_or_404(prompt_id: uuid.UUID, user: User, db: AsyncSession) -> Prompt:
    result = await db.execute(
        select(Prompt).where(Prompt.id == prompt_id, Prompt.owner_id == user.id)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("", response_model=PromptResponse, status_code=201)
async def create_prompt(
    payload: PromptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prompt = Prompt(
        name=payload.name,
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(prompt)
    await db.flush()  # get the prompt.id before creating version

    version = PromptVersion(
        prompt_id=prompt.id,
        version_number=1,
        content=payload.content,
        commit_message=payload.commit_message or "Initial version",
        model_used=payload.model_used,
        variables=extract_variables(payload.content),
    )
    db.add(version)
    await db.commit()
    await db.refresh(prompt)

    return PromptResponse(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        owner_id=prompt.owner_id,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        latest_version=PromptVersionResponse.model_validate(version),
        version_count=1,
    )


@router.get("", response_model=list[PromptResponse])
async def list_prompts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Prompt).where(Prompt.owner_id == current_user.id).order_by(Prompt.updated_at.desc())
    )
    prompts = result.scalars().all()

    response = []
    for prompt in prompts:
        # get latest version
        v_result = await db.execute(
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt.id)
            .order_by(PromptVersion.version_number.desc())
            .limit(1)
        )
        latest = v_result.scalar_one_or_none()

        # get version count
        count_result = await db.execute(
            select(func.count()).where(PromptVersion.prompt_id == prompt.id)
        )
        count = count_result.scalar()

        response.append(PromptResponse(
            id=prompt.id,
            name=prompt.name,
            description=prompt.description,
            owner_id=prompt.owner_id,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
            latest_version=PromptVersionResponse.model_validate(latest) if latest else None,
            version_count=count or 0,
        ))

    return response


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prompt = await _get_prompt_or_404(prompt_id, current_user, db)

    v_result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version_number.desc())
        .limit(1)
    )
    latest = v_result.scalar_one_or_none()

    count_result = await db.execute(
        select(func.count()).where(PromptVersion.prompt_id == prompt.id)
    )
    count = count_result.scalar()

    return PromptResponse(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        owner_id=prompt.owner_id,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        latest_version=PromptVersionResponse.model_validate(latest) if latest else None,
        version_count=count or 0,
    )


@router.patch("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: uuid.UUID,
    payload: PromptUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prompt = await _get_prompt_or_404(prompt_id, current_user, db)

    if payload.name is not None:
        prompt.name = payload.name
    if payload.description is not None:
        prompt.description = payload.description

    await db.commit()
    await db.refresh(prompt)
    return await get_prompt(prompt_id, db, current_user)


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prompt = await _get_prompt_or_404(prompt_id, current_user, db)
    await db.delete(prompt)
    await db.commit()


@router.post("/{prompt_id}/versions", response_model=PromptVersionResponse, status_code=201)
async def save_new_version(
    prompt_id: uuid.UUID,
    payload: PromptSaveVersion,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prompt = await _get_prompt_or_404(prompt_id, current_user, db)

    count_result = await db.execute(
        select(func.count()).where(PromptVersion.prompt_id == prompt.id)
    )
    current_count = count_result.scalar() or 0

    version = PromptVersion(
        prompt_id=prompt.id,
        version_number=current_count + 1,
        content=payload.content,
        commit_message=payload.commit_message,
        model_used=payload.model_used,
        variables=extract_variables(payload.content),
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionResponse])
async def list_versions(
    prompt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _get_prompt_or_404(prompt_id, current_user, db)
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version_number.desc())
    )
    return result.scalars().all()


@router.post("/interpolate", response_model=InterpolateResponse)
async def interpolate_prompt(
    payload: InterpolateRequest,
    current_user: User = Depends(get_current_user),
):
    result = interpolate(payload.content, payload.variables)
    return result
