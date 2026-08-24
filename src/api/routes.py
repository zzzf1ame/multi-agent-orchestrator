"""
FastAPI routes for the multi-agent orchestrator API.
Adapted for langgraph 1.x dict-based state.
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends

from ..models.schemas import (
    ResearchRequest, TaskResponse, TaskResult, TaskStatus,
    ResearchOutput, ArticleOutput,
)
from ..orchestrator import MultiAgentOrchestrator
from .dependencies import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["research"])

# In-memory task storage (bounded: finished tasks are pruned oldest-first)
task_storage: Dict[str, Dict[str, Any]] = {}
MAX_STORED_TASKS = int(os.getenv("MAX_STORED_TASKS", "1000"))


def _prune_task_storage() -> None:
    """Evict oldest finished tasks when storage exceeds MAX_STORED_TASKS."""
    overflow = len(task_storage) - MAX_STORED_TASKS
    if overflow <= 0:
        return
    finished = [
        t for t in task_storage.values()
        if t["status"] in (TaskStatus.COMPLETED, TaskStatus.FAILED)
    ]
    finished.sort(key=lambda t: t.get("completed_at") or t["started_at"])
    for task in finished[:overflow]:
        task_storage.pop(task["task_id"], None)


@router.post("/research", response_model=TaskResponse)
async def create_research_task(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator),
) -> TaskResponse:
    """Create a new research task (executes in background)."""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    logger.info(f"Creating task {task_id}: '{request.topic}'")

    _prune_task_storage()
    task_storage[task_id] = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "request": request.model_dump(),
        "started_at": datetime.utcnow(),
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        _execute_workflow, task_id=task_id, request=request, orchestrator=orchestrator
    )

    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message=f"Research task created for: {request.topic}",
    )


@router.get("/research/{task_id}", response_model=TaskResult)
async def get_research_task(task_id: str) -> TaskResult:
    """Get task status and results."""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_storage[task_id]
    duration = None
    if task.get("completed_at") and task.get("started_at"):
        duration = (task["completed_at"] - task["started_at"]).total_seconds()

    # Parse research/article from raw dict result
    research = None
    article = None
    result = task.get("result") or {}

    if result.get("research_output"):
        try:
            research = ResearchOutput(**result["research_output"])
        except Exception:
            pass

    if result.get("article_output"):
        try:
            article = ArticleOutput(**result["article_output"])
        except Exception:
            pass

    return TaskResult(
        task_id=task_id,
        status=task["status"],
        research=research,
        article=article,
        error=task.get("error"),
        started_at=task["started_at"],
        completed_at=task.get("completed_at"),
        duration_seconds=duration,
    )


@router.get("/research", response_model=Dict[str, Any])
async def list_research_tasks(
    status: Optional[TaskStatus] = None, limit: int = 10
) -> Dict[str, Any]:
    """List tasks with optional status filter."""
    tasks = list(task_storage.values())
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    tasks.sort(key=lambda x: x["started_at"], reverse=True)
    return {"tasks": tasks[:limit], "total": len(task_storage), "filtered": len(tasks)}


@router.delete("/research/{task_id}")
async def delete_research_task(task_id: str) -> Dict[str, str]:
    """Delete a task."""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    del task_storage[task_id]
    return {"message": f"Task {task_id} deleted"}


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_tasks": len([
            t for t in task_storage.values()
            if t["status"] in (TaskStatus.PENDING, TaskStatus.RESEARCHING, TaskStatus.WRITING)
        ]),
        "total_tasks": len(task_storage),
    }


# ===== Background execution =====

async def _execute_workflow(
    task_id: str, request: ResearchRequest, orchestrator: MultiAgentOrchestrator
) -> None:
    """Run the agent workflow in background."""
    logger.info(f"[bg] Starting workflow: {task_id}")

    try:
        task_storage[task_id]["status"] = TaskStatus.RESEARCHING

        result = await orchestrator.execute_workflow(
            topic=request.topic,
            depth=request.depth,
            max_sources=request.max_sources,
            task_id=task_id,
        )

        if result["success"]:
            task_storage[task_id].update({
                "status": TaskStatus.COMPLETED,
                "result": result["result"],
                "completed_at": datetime.utcnow(),
            })
            logger.info(f"[bg] Task {task_id} completed")
        else:
            task_storage[task_id].update({
                "status": TaskStatus.FAILED,
                "error": result.get("error", "Workflow returned no article"),
                "completed_at": datetime.utcnow(),
            })
            logger.error(f"[bg] Task {task_id} failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"[bg] Task {task_id} exception: {e}")
        task_storage[task_id].update({
            "status": TaskStatus.FAILED,
            "error": str(e),
            "completed_at": datetime.utcnow(),
        })
