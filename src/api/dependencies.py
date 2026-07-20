"""
FastAPI dependency injection — initializes LLM and orchestrator.
"""
import os
from typing import Optional
from functools import lru_cache

from ..orchestrator import MultiAgentOrchestrator


_orchestrator: Optional[MultiAgentOrchestrator] = None


@lru_cache()
def get_settings():
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "tavily_api_key": os.getenv("TAVILY_API_KEY"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }


def get_orchestrator() -> MultiAgentOrchestrator:
    """Get or create the multi-agent orchestrator instance."""
    global _orchestrator

    if _orchestrator is None:
        settings = get_settings()
        llm = None

        if settings["openai_api_key"]:
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    api_key=settings["openai_api_key"],
                    model=settings["openai_model"],
                    temperature=0.7,
                    timeout=60,
                    max_retries=2,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to init LLM: {e}")

        _orchestrator = MultiAgentOrchestrator(
            llm=llm,
            tavily_api_key=settings["tavily_api_key"],
        )

    return _orchestrator


def get_task_manager():
    """Placeholder for future Redis/database task storage."""
    return None
