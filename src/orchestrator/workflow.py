"""
LangGraph workflow orchestrator for multi-agent system.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..models.schemas import AgentState, TaskStatus, ResearchDepth
from ..agents import ResearcherAgent, WriterAgent

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """
    Orchestrates the multi-agent workflow using LangGraph.
    """
    
    def __init__(self, llm=None):
        """
        Initialize the orchestrator with agents and workflow.
        
        Args:
            llm: Language model instance
        """
        self.llm = llm
        self.researcher = ResearcherAgent(llm=llm)
        self.writer = WriterAgent(llm=llm)
        self.memory = MemorySaver()
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph workflow
        """
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("researcher", self._research_node)
        workflow.add_node("writer", self._writer_node)
        workflow.add_node("validator", self._validation_node)
        
        # Define the workflow edges
        workflow.set_entry_point("researcher")
        workflow.add_edge("researcher", "validator")
        workflow.add_conditional_edges(
            "validator",
            self._should_proceed_to_writer,
            {
                "proceed": "writer",
                "retry": "researcher",
                "end": END
            }
        )
        workflow.add_edge("writer", END)
        
        # Compile the workflow
        return workflow.compile(checkpointer=self.memory)
    
    async def _research_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute research node.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info(f"Executing research node for task: {state.task_id}")
        result = await self.researcher.research(state)
        
        # Update state with research results
        updated_state = state.dict()
        updated_state.update(result)
        
        return updated_state
    
    async def _writer_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute writer node.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info(f"Executing writer node for task: {state.task_id}")
        result = await self.writer.write_article(state)
        
        # Update state with writing results
        updated_state = state.dict()
        updated_state.update(result)
        
        return updated_state
    
    async def _validation_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Validate research output before proceeding to writer.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with validation results
        """
        logger.info(f"Validating research output for task: {state.task_id}")
        
        if not state.research_output:
            return {
                "current_step": "validation_failed",
                "errors": state.errors + ["No research output to validate"]
            }
        
        # Validate research output structure and content
        validation_errors = []
        
        # Check required fields
        if not state.research_output.summary or len(state.research_output.summary) < 50:
            validation_errors.append("Research summary too short or missing")
        
        if not state.research_output.key_findings or len(state.research_output.key_findings) < 1:
            validation_errors.append("Insufficient key findings")
        
        # Check content quality (basic validation)
        if len(state.research_output.summary.split()) < 20:
            validation_errors.append("Research summary lacks sufficient detail")
        
        if validation_errors:
            logger.warning(f"Validation failed: {validation_errors}")
            return {
                "current_step": "validation_failed",
                "errors": state.errors + validation_errors
            }
        
        logger.info("Research output validation passed")
        return {
            "current_step": "validation_passed"
        }
    
    def _should_proceed_to_writer(self, state: AgentState) -> str:
        """
        Determine next step after validation.
        
        Args:
            state: Current agent state
            
        Returns:
            Next step decision
        """
        if state.current_step == "validation_passed":
            return "proceed"
        elif state.current_step == "validation_failed" and len(state.errors) < 3:
            # Allow up to 2 retries
            return "retry"
        else:
            return "end"
    
    async def execute_workflow(
        self, 
        topic: str, 
        depth: ResearchDepth = ResearchDepth.DETAILED,
        max_sources: int = 5,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete multi-agent workflow.
        
        Args:
            topic: Research topic
            depth: Research depth level
            max_sources: Maximum number of sources
            task_id: Optional task ID (generated if not provided)
            
        Returns:
            Workflow execution result
        """
        if not task_id:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Starting workflow execution for task: {task_id}")
        
        # Initialize state
        initial_state = AgentState(
            task_id=task_id,
            topic=topic,
            depth=depth,
            max_sources=max_sources,
            current_step="initialized"
        )
        
        try:
            # Execute workflow
            config = {"configurable": {"thread_id": task_id}}
            result = await self.workflow.ainvoke(
                initial_state.dict(),
                config=config
            )
            
            logger.info(f"Workflow completed for task: {task_id}")
            return {
                "success": True,
                "task_id": task_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed for task {task_id}: {str(e)}")
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    async def get_workflow_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current workflow state for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Current workflow state or None if not found
        """
        try:
            config = {"configurable": {"thread_id": task_id}}
            state = await self.workflow.aget_state(config)
            return state.values if state else None
        except Exception as e:
            logger.error(f"Failed to get workflow state for task {task_id}: {str(e)}")
            return None