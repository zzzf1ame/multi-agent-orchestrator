"""
FastAPI dependency injection for shared resources.
"""
import os
from typing import Optional
from functools import lru_cache

from ..orchestrator import MultiAgentOrchestrator


# Global orchestrator instance
_orchestrator: Optional[MultiAgentOrchestrator] = None


@lru_cache()
def get_settings():
    """Get application settings."""
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "max_workers": int(os.getenv("MAX_WORKERS", "4")),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379")
    }


def get_orchestrator() -> MultiAgentOrchestrator:
    """
    Get or create the multi-agent orchestrator instance.
    
    Returns:
        MultiAgentOrchestrator instance
    """
    global _orchestrator
    
    if _orchestrator is None:
        # Initialize LLM if API key is available
        llm = None
        settings = get_settings()
        
        if settings["openai_api_key"]:
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    api_key=settings["openai_api_key"],
                    model="gpt-3.5-turbo",
                    temperature=0.7
                )
            except ImportError:
                # OpenAI not available, use mock LLM
                pass
        
        _orchestrator = MultiAgentOrchestrator(llm=llm)
    
    return _orchestrator


def get_task_manager():
    """
    Get task manager (placeholder for future Redis/database integration).
    
    Returns:
        Task manager instance
    """
    # TODO: Implement Redis or database-based task manager
    return None