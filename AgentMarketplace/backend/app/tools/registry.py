import re
from typing import Dict, Optional, List, Set
from app.tools.base import BaseTool
from app.tools.implementations import CalculatorTool, TextStatsTool, SearchTool
from loguru import logger

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Stop words to filter out for semantic scoring
        self._stop_words: Set[str] = {
            "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", 
            "at", "by", "from", "for", "with", "in", "on", "to", "is", "are", 
            "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did"
        }
        
        # Auto-register core tools
        self.register(CalculatorTool())
        self.register(TextStatsTool())
        self.register(SearchTool())

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
        logger.info(f"[ToolRegistry] Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def _tokenize(self, text: str) -> Set[str]:
        """Convert text to a clean set of tokens."""
        tokens = re.findall(r'\w+', text.lower())
        return {t for t in tokens if t not in self._stop_words and len(t) > 2}

    def _compute_relevance_score(self, query: str, tool: BaseTool) -> float:
        """Compute Jaccard similarity between query tokens and tool metadata."""
        query_tokens = self._tokenize(query)
        # Combine name and description for semantic context
        tool_content = f"{tool.name} {tool.description}"
        tool_tokens = self._tokenize(tool_content)
        
        if not query_tokens or not tool_tokens:
            return 0.0
            
        intersection = query_tokens.intersection(tool_tokens)
        union = query_tokens.union(tool_tokens)
        
        score = len(intersection) / len(union)
        return round(score, 4)

    def get_relevant_tools(self, query: str, requested_tool_names: Optional[List[str]] = None, threshold: float = 0.05) -> List[BaseTool]:
        """Intelligently score and filter tools based on semantic relevance."""
        logger.info(f"[ToolRegistry] Scoring tools for query: {query[:50]}...")
        
        results = []
        # Use requested list if provided, otherwise all registered tools
        search_pool = requested_tool_names if requested_tool_names else list(self._tools.keys())
        
        for tool_name in search_pool:
            tool = self._tools.get(tool_name)
            if not tool:
                continue
                
            score = self._compute_relevance_score(query, tool)
            
            # Boost score if tool name is explicitly mentioned
            if tool_name.lower() in query.lower():
                score += 0.5
            
            logger.debug(f"[ToolRegistry] Tool: {tool_name}, Initial Score: {score}")
            
            if score >= threshold:
                results.append((tool, score))
        
        # Sort by score and take top 3
        results.sort(key=lambda x: x[1], reverse=True)
        relevant = [r[0] for r in results[:3]]
        
        logger.info(f"[ToolRegistry] Selected relevant tools: {[t.name for t in relevant]}")
        return relevant

# Global registry instance
tool_registry = ToolRegistry()
