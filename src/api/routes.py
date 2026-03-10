"""
FastAPI routes for the multi-agent orchestrator API.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from ..models.schemas import (
    ResearchRequest, TaskResponse, TaskResult, TaskStatus,
    ResearchDepth
)
from ..orchestrator import MultiAgentOrchestrator
from .dependencies import get_orchestrator, get_task_manager

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["research"])

# In-memory task storage (replace with Redis/database in production)
task_storage: Dict[str, Dict[str, Any]] = {}


@router.post("/research", response_model=TaskResponse)
async def create_research_task(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator)
) -> TaskResponse:
    """
    Create a new research task.
    
    Args:
        request: Research request parameters
        background_tasks: FastAPI background tasks
        orchestrator: Multi-agent orchestrator instance
        
    Returns:
        Task creation response
    """
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Creating research task {task_id} for topic: {request.topic}")
    
    # Initialize task in storage
    task_storage[task_id] = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "request": request.dict(),
        "started_at": datetime.utcnow(),
        "result": None,
        "error": None
    }
    
    # Schedule background execution
    background_tasks.add_task(
        execute_research_workflow,
        task_id=task_id,
        request=request,
        orchestrator=orchestrator
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message=f"Research task created for topic: {request.topic}"
    )


@router.get("/research/{task_id}", response_model=TaskResult)
async def get_research_task(task_id: str) -> TaskResult:
    """
    Get research task status and results.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task result with current status
        
    Raises:
        HTTPException: If task not found
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = task_storage[task_id]
    
    # Calculate duration if completed
    duration = None
    if task_data.get("completed_at") and task_data.get("started_at"):
        duration = (task_data["completed_at"] - task_data["started_at"]).total_seconds()
    
    return TaskResult(
        task_id=task_id,
        status=task_data["status"],
        research=task_data.get("result", {}).get("research_output"),
        article=task_data.get("result", {}).get("article_output"),
        error=task_data.get("error"),
        started_at=task_data["started_at"],
        completed_at=task_data.get("completed_at"),
        duration_seconds=duration
    )


@router.get("/research", response_model=Dict[str, Any])
async def list_research_tasks(
    status: Optional[TaskStatus] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    List research tasks with optional filtering.
    
    Args:
        status: Optional status filter
        limit: Maximum number of tasks to return
        
    Returns:
        List of tasks with metadata
    """
    tasks = list(task_storage.values())
    
    # Filter by status if provided
    if status:
        tasks = [task for task in tasks if task["status"] == status]
    
    # Sort by creation time (newest first)
    tasks.sort(key=lambda x: x["started_at"], reverse=True)
    
    # Apply limit
    tasks = tasks[:limit]
    
    return {
        "tasks": tasks,
        "total": len(task_storage),
        "filtered": len(tasks)
    }


@router.delete("/research/{task_id}")
async def delete_research_task(task_id: str) -> Dict[str, str]:
    """
    Delete a research task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If task not found
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del task_storage[task_id]
    
    return {"message": f"Task {task_id} deleted successfully"}


async def execute_research_workflow(
    task_id: str,
    request: ResearchRequest,
    orchestrator: MultiAgentOrchestrator
) -> None:
    """
    Execute research workflow in background.
    
    Args:
        task_id: Task identifier
        request: Research request parameters
        orchestrator: Multi-agent orchestrator instance
    """
    logger.info(f"Starting workflow execution for task: {task_id}")
    
    try:
        # Update status to researching
        task_storage[task_id]["status"] = TaskStatus.RESEARCHING
        
        # Execute workflow
        result = await orchestrator.execute_workflow(
            topic=request.topic,
            depth=request.depth,
            max_sources=request.max_sources,
            task_id=task_id
        )
        
        if result["success"]:
            # Update task with successful result
            task_storage[task_id].update({
                "status": TaskStatus.COMPLETED,
                "result": result["result"],
                "completed_at": datetime.utcnow()
            })
            logger.info(f"Task {task_id} completed successfully")
        else:
            # Update task with error
            task_storage[task_id].update({
                "status": TaskStatus.FAILED,
                "error": result.get("error", "Unknown error"),
                "completed_at": datetime.utcnow()
            })
            logger.error(f"Task {task_id} failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Workflow execution failed for task {task_id}: {str(e)}")
        task_storage[task_id].update({
            "status": TaskStatus.FAILED,
            "error": str(e),
            "completed_at": datetime.utcnow()
        })


# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_tasks": len([
            task for task in task_storage.values()
            if task["status"] in [TaskStatus.PENDING, TaskStatus.RESEARCHING, TaskStatus.WRITING]
        ]),
        "total_tasks": len(task_storage)
    }