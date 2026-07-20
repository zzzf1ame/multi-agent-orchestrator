"""
Pydantic models for API validation and LangGraph state definition.
Upgraded for langgraph 1.x: graph state uses TypedDict + Annotated reducers.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, field_validator
import operator


# ===== Enums =====

class TaskStatus(str, Enum):
    PENDING = "pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchDepth(str, Enum):
    BRIEF = "brief"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


# ===== API Request/Response Models =====

class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500, description="Research topic")
    depth: ResearchDepth = Field(default=ResearchDepth.DETAILED)
    max_sources: int = Field(default=5, ge=1, le=20)

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()


class ResearchOutput(BaseModel):
    topic: str
    summary: str = Field(..., min_length=50)
    key_findings: List[str] = Field(..., min_length=1)
    sources: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ArticleOutput(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    content: str = Field(..., min_length=100)
    word_count: int = Field(..., ge=0)
    sections: List[str] = Field(default_factory=list)
    research_reference: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    research: Optional[ResearchOutput] = None
    article: Optional[ArticleOutput] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class WebSocketMessage(BaseModel):
    type: str
    task_id: Optional[str] = None
    status: Optional[TaskStatus] = None
    data: Optional[Dict[str, Any]] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===== LangGraph State (TypedDict + reducers for langgraph 1.x) =====

def _merge_errors(existing: List[str], new: List[str]) -> List[str]:
    """Reducer: append new errors to existing list."""
    return existing + new


class AgentState(TypedDict, total=False):
    """
    Shared state between agents in LangGraph 1.x.
    Uses Annotated reducers so partial node returns merge correctly.
    """
    task_id: str
    topic: str
    depth: str
    max_sources: int
    research_output: Optional[Dict[str, Any]]
    article_output: Optional[Dict[str, Any]]
    current_step: str
    errors: Annotated[List[str], _merge_errors]
    metadata: Dict[str, Any]
