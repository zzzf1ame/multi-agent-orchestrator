"""
Tests for agent implementations.
"""
import pytest
from datetime import datetime

from src.agents import ResearcherAgent, WriterAgent
from src.models.schemas import AgentState, ResearchDepth, ResearchOutput


class TestResearcherAgent:
    """Test cases for ResearcherAgent."""
    
    @pytest.fixture
    def researcher(self):
        """Create ResearcherAgent instance."""
        return ResearcherAgent()
    
    @pytest.fixture
    def sample_state(self):
        """Create sample agent state."""
        return AgentState(
            task_id="test_task_123",
            topic="Artificial Intelligence trends",
            depth=ResearchDepth.DETAILED,
            max_sources=3
        )
    
    @pytest.mark.asyncio
    async def test_research_success(self, researcher, sample_state):
        """Test successful research execution."""
        result = await researcher.research(sample_state)
        
        assert "research_output" in result
        assert "current_step" in result
        assert result["current_step"] == "research_completed"
        
        research_output = result["research_output"]
        assert isinstance(research_output, ResearchOutput)
        assert research_output.topic == sample_state.topic
        assert len(research_output.key_findings) > 0
        assert len(research_output.sources) > 0
    
    @pytest.mark.asyncio
    async def test_research_output_validation(self, researcher, sample_state):
        """Test research output validation."""
        result = await researcher.research(sample_state)
        research_output = result["research_output"]
        
        # Test Pydantic validation
        assert len(research_output.summary) >= 50
        assert len(research_output.key_findings) >= 1
        assert isinstance(research_output.sources, list)
        assert isinstance(research_output.timestamp, datetime)
    
    def test_researcher_repr(self, researcher):
        """Test researcher string representation."""
        assert "ResearcherAgent" in repr(researcher)
        assert researcher.name == "Researcher"


class TestWriterAgent:
    """Test cases for WriterAgent."""
    
    @pytest.fixture
    def writer(self):
        """Create WriterAgent instance."""
        return WriterAgent()
    
    @pytest.fixture
    def sample_state_with_research(self):
        """Create sample agent state with research output."""
        research_output = ResearchOutput(
            topic="AI trends",
            summary="AI is rapidly evolving with new developments in machine learning and automation.",
            key_findings=[
                "Generative AI adoption increased significantly",
                "Multi-modal models are becoming mainstream",
                "AI ethics and governance are critical concerns"
            ],
            sources=[
                {"title": "AI Report 2024", "url": "https://example.com/report"}
            ]
        )
        
        return AgentState(
            task_id="test_task_123",
            topic="AI trends",
            depth=ResearchDepth.DETAILED,
            max_sources=3,
            research_output=research_output
        )
    
    @pytest.mark.asyncio
    async def test_write_article_success(self, writer, sample_state_with_research):
        """Test successful article writing."""
        result = await writer.write_article(sample_state_with_research)
        
        assert "article_output" in result
        assert "current_step" in result
        assert result["current_step"] == "writing_completed"
        
        article_output = result["article_output"]
        assert len(article_output.title) >= 10
        assert len(article_output.content) >= 100
        assert article_output.word_count > 0
        assert len(article_output.sections) > 0
    
    @pytest.mark.asyncio
    async def test_write_article_no_research(self, writer):
        """Test article writing without research output."""
        state = AgentState(
            task_id="test_task_123",
            topic="AI trends",
            depth=ResearchDepth.DETAILED,
            max_sources=3
        )
        
        result = await writer.write_article(state)
        
        assert "errors" in result
        assert "current_step" in result
        assert result["current_step"] == "writing_failed"
        assert len(result["errors"]) > 0
    
    def test_writer_repr(self, writer):
        """Test writer string representation."""
        assert "WriterAgent" in repr(writer)
        assert writer.name == "Writer"
    
    def test_build_article_content(self, writer, sample_state_with_research):
        """Test article content building."""
        research = sample_state_with_research.research_output
        sections = ["Introduction", "Analysis", "Conclusion"]
        
        content = writer._build_article_content(research, sections)
        
        assert isinstance(content, str)
        assert len(content) > 100
        assert "Executive Summary" in content
        assert "Key Findings" in content
        assert research.topic in content