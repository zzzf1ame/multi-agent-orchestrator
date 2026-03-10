"""
Writer Agent - Creates structured articles based on research data.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from ..models.schemas import ArticleOutput, AgentState, ResearchOutput

logger = logging.getLogger(__name__)


class WriterAgent:
    """
    Writer agent responsible for creating well-structured articles
    based on research output.
    """
    
    def __init__(self, llm=None):
        """
        Initialize the Writer agent.
        
        Args:
            llm: Language model instance (OpenAI, Anthropic, etc.)
        """
        self.llm = llm
        self.name = "Writer"
        
    async def write_article(self, state: AgentState) -> Dict[str, Any]:
        """
        Create article based on research output.
        
        Args:
            state: Current agent state containing research output
            
        Returns:
            Updated state with article output
        """
        logger.info(f"Writer starting article creation for: {state.topic}")
        
        if not state.research_output:
            error_msg = "No research output available for writing"
            logger.error(error_msg)
            return {
                "errors": state.errors + [error_msg],
                "current_step": "writing_failed"
            }
        
        try:
            # Generate article based on research
            article_data = await self._generate_article(
                research=state.research_output,
                topic=state.topic
            )
            
            # Validate and structure output using Pydantic
            article_output = ArticleOutput(
                title=article_data["title"],
                content=article_data["content"],
                word_count=len(article_data["content"].split()),
                sections=article_data["sections"],
                research_reference=state.task_id
            )
            
            logger.info(f"Article completed: {article_output.word_count} words")
            
            return {
                "article_output": article_output,
                "current_step": "writing_completed"
            }
            
        except Exception as e:
            logger.error(f"Writing failed: {str(e)}")
            return {
                "errors": state.errors + [f"Writing error: {str(e)}"],
                "current_step": "writing_failed"
            }
    
    async def _generate_article(
        self, 
        research: ResearchOutput, 
        topic: str
    ) -> Dict[str, Any]:
        """
        Generate article content using LLM.
        
        Args:
            research: Research output from Researcher agent
            topic: Article topic
            
        Returns:
            Article data dictionary
        """
        # TODO: Replace with actual LLM API call
        # Example: response = await self.llm.ainvoke(prompt)
        
        # Create structured article based on research
        title = f"Comprehensive Analysis: {topic}"
        
        sections = [
            "Executive Summary",
            "Key Findings",
            "Detailed Analysis",
            "Implications",
            "Conclusion"
        ]
        
        content = self._build_article_content(research, sections)
        
        return {
            "title": title,
            "content": content,
            "sections": sections
        }
    
    def _build_article_content(
        self, 
        research: ResearchOutput, 
        sections: list
    ) -> str:
        """
        Build structured article content.
        
        Args:
            research: Research output
            sections: Article sections
            
        Returns:
            Complete article content
        """
        content_parts = []
        
        # Executive Summary
        content_parts.append("## Executive Summary\n")
        content_parts.append(f"{research.summary}\n\n")
        
        # Key Findings
        content_parts.append("## Key Findings\n")
        for i, finding in enumerate(research.key_findings, 1):
            content_parts.append(f"{i}. {finding}\n")
        content_parts.append("\n")
        
        # Detailed Analysis
        content_parts.append("## Detailed Analysis\n")
        content_parts.append(
            f"Our comprehensive analysis of {research.topic} reveals several "
            f"critical insights that organizations should consider. The research "
            f"indicates significant developments in this area, with implications "
            f"for both current operations and future strategic planning.\n\n"
        )
        
        # Expand on each key finding
        for finding in research.key_findings:
            content_parts.append(f"### {finding}\n")
            content_parts.append(
                f"This finding represents a crucial aspect of {research.topic}. "
                f"The implications extend beyond immediate applications to "
                f"long-term strategic considerations. Organizations should "
                f"evaluate their current capabilities and develop appropriate "
                f"response strategies.\n\n"
            )
        
        # Implications
        content_parts.append("## Implications\n")
        content_parts.append(
            f"The research findings on {research.topic} have several important "
            f"implications for stakeholders:\n\n"
            f"- **Strategic Planning**: Organizations need to incorporate these "
            f"insights into their long-term planning processes.\n"
            f"- **Resource Allocation**: Investment priorities may need to be "
            f"adjusted based on emerging trends.\n"
            f"- **Risk Management**: New challenges require updated risk "
            f"assessment and mitigation strategies.\n"
            f"- **Competitive Advantage**: Early adoption of best practices "
            f"can provide significant market advantages.\n\n"
        )
        
        # Conclusion
        content_parts.append("## Conclusion\n")
        content_parts.append(
            f"This analysis of {research.topic} demonstrates the importance of "
            f"staying informed about developments in this rapidly evolving field. "
            f"The key findings highlight both opportunities and challenges that "
            f"organizations must navigate to remain competitive and effective.\n\n"
            f"Moving forward, continued monitoring and adaptation will be essential "
            f"for success in this dynamic environment.\n\n"
        )
        
        # Sources
        if research.sources:
            content_parts.append("## References\n")
            for i, source in enumerate(research.sources, 1):
                content_parts.append(
                    f"{i}. {source.get('title', 'Unknown Title')} - "
                    f"{source.get('url', 'No URL')}\n"
                )
        
        return "".join(content_parts)
    
    def __repr__(self) -> str:
        return f"<WriterAgent(name='{self.name}')>"