"""
Writer Agent - Creates structured articles from research data using LLM.
Falls back to template-based generation if LLM is unavailable.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WriterAgent:
    """
    Writer agent: takes research output and produces a structured article.
    Uses LLM for generation when available, otherwise template fallback.
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.name = "Writer"

    async def write_article(
        self, topic: str, research_output: Dict[str, Any], task_id: str = ""
    ) -> Dict[str, Any]:
        """
        Generate article from research output.
        Returns partial state dict for LangGraph.
        """
        logger.info(f"[Writer] topic='{topic}'")

        if not research_output:
            return {
                "errors": ["No research output available for writing"],
                "current_step": "writing_failed",
            }

        try:
            if self.llm:
                article = await self._generate_with_llm(topic, research_output)
            else:
                article = self._generate_template(topic, research_output)

            return {
                "article_output": article,
                "current_step": "writing_completed",
            }

        except Exception as e:
            logger.error(f"[Writer] failed: {e}")
            return {
                "errors": [f"Writing error: {str(e)}"],
                "current_step": "writing_failed",
            }

    async def _generate_with_llm(self, topic: str, research: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to write a polished article from research data."""
        summary = research.get("summary", "")
        findings = research.get("key_findings", [])
        sources = research.get("sources", [])

        findings_text = "\n".join(f"- {f}" for f in findings)
        sources_text = "\n".join(f"- [{s.get('title', '')}]({s.get('url', '')})" for s in sources)

        prompt = f"""You are a professional technical writer. Write a well-structured article based on this research:

TOPIC: {topic}

RESEARCH SUMMARY:
{summary}

KEY FINDINGS:
{findings_text}

SOURCES:
{sources_text}

Write a complete article with these sections:
1. Title (compelling, specific)
2. Executive Summary (2-3 sentences)
3. Key Findings (expand each finding into a paragraph)
4. Analysis & Implications
5. Conclusion

Format your response as:
TITLE: <article title>
CONTENT:
<full article in markdown format>
"""
        response = await self.llm.ainvoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)

        title, content = self._parse_article(text, topic)
        sections = ["Executive Summary", "Key Findings", "Analysis & Implications", "Conclusion"]

        return {
            "title": title,
            "content": content,
            "word_count": len(content.split()),
            "sections": sections,
            "research_reference": research.get("topic", topic),
        }

    def _generate_template(self, topic: str, research: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: build article from template (no LLM needed)."""
        summary = research.get("summary", "No summary available.")
        findings = research.get("key_findings", [])
        sources = research.get("sources", [])

        title = f"Research Report: {topic}"
        sections = ["Executive Summary", "Key Findings", "Analysis", "Conclusion", "References"]

        parts = [
            f"# {title}\n",
            "## Executive Summary\n",
            f"{summary}\n\n",
            "## Key Findings\n",
        ]
        for i, finding in enumerate(findings, 1):
            parts.append(f"### {i}. {finding}\n")
            parts.append(f"This finding highlights an important aspect of {topic} "
                         f"that warrants further attention and investigation.\n\n")

        parts.append("## Analysis & Implications\n")
        parts.append(f"The research on {topic} reveals several important patterns. "
                     f"Organizations and researchers should consider these findings "
                     f"when planning future work in this area.\n\n")

        parts.append("## Conclusion\n")
        parts.append(f"This report synthesizes current knowledge on {topic} "
                     f"based on {len(sources)} sources. Continued monitoring and "
                     f"research in this area is recommended.\n\n")

        if sources:
            parts.append("## References\n")
            for i, s in enumerate(sources, 1):
                parts.append(f"{i}. [{s.get('title', 'Untitled')}]({s.get('url', '#')})\n")

        content = "".join(parts)

        return {
            "title": title,
            "content": content,
            "word_count": len(content.split()),
            "sections": sections,
            "research_reference": topic,
        }

    def _parse_article(self, text: str, topic: str) -> tuple:
        """Parse LLM output into (title, content)."""
        title = f"Research Report: {topic}"
        content = text

        lines = text.strip().split("\n")
        content_start = 0

        for i, line in enumerate(lines):
            if line.strip().upper().startswith("TITLE:"):
                title = line.strip()[len("TITLE:"):].strip()
            elif line.strip().upper().startswith("CONTENT:"):
                content_start = i + 1
                break

        if content_start > 0:
            content = "\n".join(lines[content_start:]).strip()

        # Ensure minimum content length
        if len(content) < 100:
            content = text

        return title, content

    def __repr__(self) -> str:
        return f"<WriterAgent(llm={'yes' if self.llm else 'no'})>"
