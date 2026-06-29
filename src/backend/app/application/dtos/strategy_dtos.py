from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StrategyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    category: str = Field(..., min_length=1, max_length=32)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    is_template: bool = False


class StrategyUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class StrategyResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    is_template: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
