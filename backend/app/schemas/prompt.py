from pydantic import BaseModel
import uuid
from datetime import datetime


# --- Prompt Version Schemas ---

class PromptVersionBase(BaseModel):
    content: str
    commit_message: str | None = None
    model_used: str | None = None


class PromptVersionResponse(PromptVersionBase):
    id: uuid.UUID
    prompt_id: uuid.UUID
    version_number: int
    variables: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Prompt Schemas ---

class PromptCreate(BaseModel):
    name: str
    description: str | None = None
    content: str
    commit_message: str | None = "Initial version"
    model_used: str | None = None


class PromptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class PromptSaveVersion(BaseModel):
    content: str
    commit_message: str | None = None
    model_used: str | None = None


class PromptResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    latest_version: PromptVersionResponse | None = None
    version_count: int = 0

    model_config = {"from_attributes": True}


# --- Variable Interpolation ---

class InterpolateRequest(BaseModel):
    content: str
    variables: dict[str, str]


class InterpolateResponse(BaseModel):
    result: str
    variables_found: list[str]
    variables_missing: list[str]
