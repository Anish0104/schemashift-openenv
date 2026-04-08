from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}


class APICall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str
    endpoint: str
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    body: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        method = value.upper()
        if method not in ALLOWED_METHODS:
            raise ValueError(f"method must be one of {sorted(ALLOWED_METHODS)}")
        return method

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("endpoint must start with '/'")
        return value


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_index: int
    rewritten_call: APICall


class CallResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_index: int
    v1_call: APICall
    submitted_call: Optional[APICall] = None
    score: float = 0.0
    feedback: str = ""
    completed: bool = False


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    task_name: str
    description: str
    migration_guide: str
    v1_calls: List[APICall]
    call_results: List[CallResult]
    pending_indices: List[int]
    current_score: float
    step_count: int
    max_steps: int
    done: bool


class Reward(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float
    breakdown: Dict[str, float] = Field(default_factory=dict)
    message: str


class StepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int = Field(default=1, ge=1, le=3)


class StateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    task_name: str
    step_count: int
    current_score: float
    pending_count: int
    total_calls: int
    done: bool
