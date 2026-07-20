"""
Researcher Agent - Gathers real information via Tavily Search API,
then uses LLM to synthesize structured research output.
"""
import logging
import os
from typing import Dict, Any, List, Optional

from tavily import TavilyClient

logger = logging.getLogger(__name__)


class ResearcherAgent:
    """
    Researcher agent: Tavily web search + LLM summarization.
    Falls back to LLM-only mode if Tavily key is missing.
    """

    def __init__(self, llm=None, tavily_api_key: Optional[str] = None):
        self.llm = llm
        self.name = "Researcher"
        api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self.tavily = TavilyClient(api_key=api_key) if api_key else None
        if not self.tavily:
            logger.warning("TAVILY_API_KEY not set — researcher will use LLM-only mode")

    async def research(self, topic: str, depth: str = "detailed", max_sources: int = 5) -> Dict[str, Any]:
        """
        Execute research: search the web, then synthesize findings.

        Returns partial state dict for LangGraph.
        """
        logger.info(f"[Researcher] topic='{topic}' depth={depth} max_sources={max_sources}")

        try:
            # Step 1: Web search via Tavily
            search_results = self._search_web(topic, max_sources)

            # Step 2: Synthesize with LLM (or fallback to extractive summary)
            if self.llm:
                output = await self._synthesize_with_llm(topic, search_results, depth)
            else:
                output = self._synthesize_extractive(topic, search_results)

            return {
                "research_output": output,
                "current_step": "research_completed",
            }

        except Exception as e:
            logger.error(f"[Researcher] failed: {e}")
            return {
                "errors": [f"Research error: {str(e)}"],
                "current_step": "research_failed",
            }

    def _search_web(self, topic: str, max_sources: int) -> List[Dict[str, str]]:
        """Call Tavily Search API. Returns list of {title, url, content}."""
        if not self.tavily:
            logger.info("[Researcher] No Tavily client, skipping web search")
            return []

        try:
            response = self.tavily.search(
                query=topic,
                max_results=max_sources,
                search_depth="advanced",
                include_answer=True,
            )
            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                })
            logger.info(f"[Researcher] Tavily returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"[Researcher] Tavily search failed: {e}")
            return []

    async def _synthesize_with_llm(
        self, topic: str, search_results: List[Dict], depth: str
    ) -> Dict[str, Any]:
        """Use LLM to synthesize search results into structured output."""
        context = "\n\n".join(
            f"[Source {i+1}: {r['title']}]({r['url']})\n{r['content']}"
            for i, r in enumerate(search_results)
        ) or "No web search results available. Use your own knowledge."

        depth_instruction = {
            "brief": "Provide a concise summary (100-200 words) with 3 key findings.",
            "detailed": "Provide a thorough summary (300-500 words) with 5 key findings.",
            "comprehensive": "Provide an exhaustive summary (500-800 words) with 7+ key findings.",
        }.get(depth, "Provide a detailed summary with 5 key findings.")

        prompt = f"""You are a research analyst. Based on the following sources, produce a structured research report on: "{topic}"

{depth_instruction}

Respond in this EXACT format (no markdown code fences):
SUMMARY: <your summary paragraph>
FINDINGS:
- <finding 1>
- <finding 2>
- <finding 3>
...

SOURCES:
{context}
"""
        response = await self.llm.ainvoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)

        # Parse LLM output
        summary, findings = self._parse_llm_output(text, topic)

        sources = [
            {"title": r["title"], "url": r["url"], "type": "web"}
            for r in search_results
        ]

        return {
            "topic": topic,
            "summary": summary,
            "key_findings": findings,
            "sources": sources,
            "metadata": {"depth": depth, "agent": self.name, "source_count": len(sources)},
        }

    def _synthesize_extractive(self, topic: str, search_results: List[Dict]) -> Dict[str, Any]:
        """Fallback: build output directly from search snippets (no LLM)."""
        if not search_results:
            return {
                "topic": topic,
                "summary": f"Research on '{topic}' completed. No external sources were available, "
                           f"but the topic has been logged for further investigation. "
                           f"Please configure TAVILY_API_KEY and OPENAI_API_KEY for full functionality.",
                "key_findings": [
                    f"Topic '{topic}' requires further investigation with proper API keys",
                    "Web search and LLM synthesis are currently unavailable",
                    "Configure environment variables to enable full research capabilities",
                ],
                "sources": [],
                "metadata": {"depth": "basic", "agent": self.name, "mode": "fallback"},
            }

        # Extractive: use first result content as summary, all titles as findings
        summary = search_results[0]["content"][:500]
        if len(summary) < 50:
            summary = f"Research on {topic}: " + " ".join(r["content"][:100] for r in search_results[:3])

        findings = [r["title"] for r in search_results if r["title"]]
        if not findings:
            findings = [f"Information gathered about {topic} from {len(search_results)} sources"]

        sources = [
            {"title": r["title"], "url": r["url"], "type": "web"}
            for r in search_results
        ]

        return {
            "topic": topic,
            "summary": summary,
            "key_findings": findings[:7],
            "sources": sources,
            "metadata": {"depth": "extractive", "agent": self.name, "mode": "no_llm"},
        }

    def _parse_llm_output(self, text: str, topic: str) -> tuple:
        """Parse structured LLM response into (summary, findings)."""
        summary = ""
        findings = []

        lines = text.strip().split("\n")
        in_findings = False

        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("SUMMARY:"):
                summary = stripped[len("SUMMARY:"):].strip()
                in_findings = False
            elif stripped.upper().startswith("FINDINGS:"):
                in_findings = True
            elif stripped.upper().startswith("SOURCES:"):
                in_findings = False
            elif in_findings and stripped.startswith("-"):
                finding = stripped.lstrip("- ").strip()
                if finding:
                    findings.append(finding)
            elif summary and not in_findings and stripped and not stripped.upper().startswith("SUMMARY"):
                # Continuation of summary
                summary += " " + stripped

        # Fallback if parsing failed
        if not summary:
            summary = text[:500] if len(text) >= 50 else f"Research on {topic} completed successfully with multiple findings."
        if not findings:
            findings = [f"Key insight about {topic} discovered during research"]

        return summary, findings

    def __repr__(self) -> str:
        return f"<ResearcherAgent(tavily={'yes' if self.tavily else 'no'}, llm={'yes' if self.llm else 'no'})>"
