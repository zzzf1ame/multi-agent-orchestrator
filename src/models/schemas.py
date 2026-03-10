"""
Pydantic models for data validation and serialization.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchDepth(str, Enum):
    """Research depth level."""
    BRIEF = "brief"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class ResearchRequest(BaseModel):
    """Request model for research task."""
    topic: str = Field(..., min_length=3, max_length=500, description="Research topic")
    depth: ResearchDepth = Field(default=ResearchDepth.DETAILED, description="Research depth")
    max_sources: int = Field(default=5, ge=1, le=20, description="Maximum number of sources")
    
    @validator('topic')
    def validate_topic(cls, v):
        if not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()


class ResearchOutput(BaseModel):
    """Structured output from Researcher agent."""
    topic: str = Field(..., description="Research topic")
    summary: str = Field(..., min_length=50, description="Research summary")
    key_findings: List[str] = Field(..., min_items=1, description="Key findings")
    sources: List[Dict[str, str]] = Field(default_factory=list, description="Source references")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "AI trends 2024",
                "summary": "Artificial Intelligence continues to evolve...",
                "key_findings": [
                    "Generative AI adoption increased by 300%",
                    "Multi-modal models are becoming mainstream"
                ],
                "sources": [
                    {"title": "AI Report 2024", "url": "https://example.com"}
                ],
                "metadata": {"confidence": 0.95}
            }
        }


class ArticleOutput(BaseModel):
    """Structured output from Writer agent."""
    title: str = Field(..., min_length=10, max_length=200)
    content: str = Field(..., min_length=100)
    word_count: int = Field(..., ge=0)
    sections: List[str] = Field(default_factory=list)
    research_reference: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Future of AI in 2024",
                "content": "In 2024, artificial intelligence...",
                "word_count": 1500,
                "sections": ["Introduction", "Key Trends", "Conclusion"],
                "research_reference": "research_123"
            }
        }


class TaskResponse(BaseModel):
    """Response model for task creation."""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskResult(BaseModel):
    """Complete task result."""
    task_id: str
    status: TaskStatus
    research: Optional[ResearchOutput] = None
    article: Optional[ArticleOutput] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str = Field(..., description="Message type")
    task_id: Optional[str] = None
    status: Optional[TaskStatus] = None
    data: Optional[Dict[str, Any]] = None
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "status_update",
                "task_id": "task_123",
                "status": "researching",
                "message": "Researcher agent is gathering information...",
                "data": {"progress": 50}
            }
        }


class AgentState(BaseModel):
    """Shared state between agents in LangGraph."""
    task_id: str
    topic: str
    depth: ResearchDepth
    max_sources: int
    research_output: Optional[ResearchOutput] = None
    article_output: Optional[ArticleOutput] = None
    current_step: str = "initialized"
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
