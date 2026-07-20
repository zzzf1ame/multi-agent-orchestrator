"""
LangGraph 1.x workflow orchestrator for multi-agent system.
Upgraded from langgraph 0.0.26 to 1.2.x — uses TypedDict state + Annotated reducers.
"""
import logging
from typing import Dict, Any, Optional
import uuid

from langgraph.graph import StateGraph, END

from ..models.schemas import AgentState, ResearchDepth
from ..agents import ResearcherAgent, WriterAgent

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """
    Orchestrates the multi-agent workflow using LangGraph 1.x.
    Flow: researcher -> validator -> (proceed|retry|end) -> writer -> END
    """

    def __init__(self, llm=None, tavily_api_key: Optional[str] = None):
        self.llm = llm
        self.researcher = ResearcherAgent(llm=llm, tavily_api_key=tavily_api_key)
        self.writer = WriterAgent(llm=llm)
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build and compile the LangGraph StateGraph."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("researcher", self._research_node)
        workflow.add_node("validator", self._validation_node)
        workflow.add_node("writer", self._writer_node)

        # Entry point
        workflow.set_entry_point("researcher")

        # Edges
        workflow.add_edge("researcher", "validator")
        workflow.add_conditional_edges(
            "validator",
            self._route_after_validation,
            {
                "proceed": "writer",
                "retry": "researcher",
                "end": END,
            },
        )
        workflow.add_edge("writer", END)

        return workflow.compile()

    # ===== Node functions =====

    async def _research_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute research agent."""
        logger.info(f"[researcher] task={state['task_id']} topic='{state['topic']}'")
        result = await self.researcher.research(
            topic=state["topic"],
            depth=state.get("depth", "detailed"),
            max_sources=state.get("max_sources", 5),
        )
        return result

    async def _validation_node(self, state: AgentState) -> Dict[str, Any]:
        """Validate research output quality."""
        research = state.get("research_output")

        if not research:
            return {
                "current_step": "validation_failed",
                "errors": ["No research output to validate"],
            }

        errors = []
        summary = research.get("summary", "")
        findings = research.get("key_findings", [])

        if len(summary) < 50:
            errors.append("Research summary too short (<50 chars)")
        if len(findings) < 1:
            errors.append("No key findings produced")

        if errors:
            logger.warning(f"[validator] failed: {errors}")
            return {"current_step": "validation_failed", "errors": errors}

        logger.info("[validator] passed")
        return {"current_step": "validation_passed"}

    async def _writer_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute writer agent."""
        logger.info(f"[writer] task={state['task_id']}")
        result = await self.writer.write_article(
            topic=state["topic"],
            research_output=state.get("research_output", {}),
            task_id=state.get("task_id", ""),
        )
        return result

    # ===== Routing logic =====

    def _route_after_validation(self, state: AgentState) -> str:
        """Decide next step after validation."""
        if state.get("current_step") == "validation_passed":
            return "proceed"
        # Allow up to 2 retries
        if len(state.get("errors", [])) < 3:
            return "retry"
        return "end"

    # ===== Public API =====

    async def execute_workflow(
        self,
        topic: str,
        depth: ResearchDepth = ResearchDepth.DETAILED,
        max_sources: int = 5,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the full research → validate → write pipeline."""
        if not task_id:
            task_id = f"task_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting workflow: task={task_id} topic='{topic}'")

        initial_state: AgentState = {
            "task_id": task_id,
            "topic": topic,
            "depth": depth.value if isinstance(depth, ResearchDepth) else depth,
            "max_sources": max_sources,
            "research_output": None,
            "article_output": None,
            "current_step": "initialized",
            "errors": [],
            "metadata": {},
        }

        try:
            result = await self.workflow.ainvoke(initial_state)
            success = result.get("article_output") is not None
            return {
                "success": success,
                "task_id": task_id,
                "result": result,
            }
        except Exception as e:
            logger.error(f"Workflow failed for task {task_id}: {e}")
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
            }
