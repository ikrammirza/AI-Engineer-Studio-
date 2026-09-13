from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PromptCreate(BaseModel):
    name: str


class PromptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime

class PromptVersionCreate(BaseModel):
    content: str


class PromptVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt_id: int
    version_number: int
    content: str
    created_at: datetime

class PromptTestRequest(BaseModel):
    variables: dict[str, str] = {}
    model: str = "qwen2.5-coder:7b"


class PromptTestResponse(BaseModel):
    rendered_prompt: str
    response: str
    model: str