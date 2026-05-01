import logging
import asyncio
import re
import time
from typing import Dict, Any, List
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Performs mathematical calculations. Supporting +, -, *, /, **, and parentheses.",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The math expression to evaluate"}
                },
                "required": ["expression"]
            }
        )

    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        expr = input_data.get("expression", "")
        if not re.match(r"^[0-9+\-*/().\s**]+$", expr):
             return {"error": "Invalid characters in expression", "status": "failed"}
        
        try:
            result = eval(expr, {"__builtins__": None}, {})
            return {"result": str(result), "status": "success"}
        except Exception as e:
            return {"error": str(e), "status": "failed"}

class TextStatsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="text_stats",
            description="Analyzes text and returns word count, character count, and sentence count.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to analyze"}
                },
                "required": ["text"]
            }
        )

    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("text", "")
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        return {
            "word_count": len(words),
            "char_count": len(text),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "status": "success"
        }

class SearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="search",
            description="Real-time web search tool to retrieve information about a topic. Use this ONLY when you need recent or real-world data not present in your knowledge base.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            },
            timeout=5.0 # Set custom 5-second timeout for web operations
        )
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 600 # 10 minutes session cache

    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "").strip()
        if not query:
            return {"error": "Query is required", "status": "failed"}

        # 1. Check in-memory cache
        current_time = time.time()
        if query in self._cache:
            cached = self._cache[query]
            if current_time - cached["timestamp"] < self._cache_ttl:
                logger.info(f"[SearchTool] Cache hit for query: {query}")
                return cached["data"]

        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            
            logger.info(f"[SearchTool] Executing real-time search for: {query}")
            start_t = time.perf_counter()
            
            # Using synchronous wrap as DDGS can be sensitive to event loop states
            loop = asyncio.get_event_loop()
            def search():
                # We use the 'ddgs' package if available, else 'duckduckgo_search'
                # The latest 'ddgs' package provides the DDGS class
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                    return results

            results = await loop.run_in_executor(None, search)
            latency = time.perf_counter() - start_t
            
            if not results:
                logger.warning(f"[SearchTool] No results for: {query}")
                return {"results": [], "summary": "No web results found.", "status": "success"}

            # 2. Structured Result Aggregation
            formatted_results = []
            snippets = []
            for r in results:
                res_obj = {
                    "title": r.get("title", "No Title"),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "url": r.get("href", r.get("link", ""))
                }
                formatted_results.append(res_obj)
                snippets.append(res_obj["snippet"])
            
            # 3. Concise Combined Summary
            summary = f"Found {len(results)} results in {latency:.2f}s. Top sources include {formatted_results[0]['title']}. Context: {' '.join(snippets[:2])}..."
            
            output_data = {
                "results": formatted_results,
                "summary": summary,
                "status": "success",
                "metadata": {
                    "query": query,
                    "count": len(results),
                    "latency": f"{latency:.2f}s"
                }
            }

            # 4. Update cache
            self._cache[query] = {
                "timestamp": current_time,
                "data": output_data
            }

            logger.info(f"[SearchTool] Completed search for: {query} ({len(results)} results, {latency:.2f}s)")
            return output_data

        except ImportError:
            logger.error("[SearchTool] Dependency 'duckduckgo-search' or 'ddgs' missing.")
            return {"error": "Search engine dependency missing.", "status": "failed"}
        except Exception as e:
            logger.exception(f"[SearchTool] Search failure for query '{query}': {str(e)}")
            return {"error": f"Search failed: {str(e)}", "status": "failed"}
