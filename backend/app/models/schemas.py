from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = Field(default=None, max_length=120)


class Incident(BaseModel):
    problem: str | None = None
    category: str | None = None
    technology: str | None = None
    error: str | None = None
    root_cause: str | None = None
    solution: str | None = None
    outcome: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str | None = None
    incident_detected: bool
    category: str | None = None
    memory_used: bool = False
    memory_status: str = "available"
    relevant_memories: list[dict[str, Any]] = Field(default_factory=list)
    incident: Incident | None = None


class MemorySummary(BaseModel):
    technologies: list[str]
    frequent_problems: list[str]
    successful_solutions: list[str]
    incidents_count: int
