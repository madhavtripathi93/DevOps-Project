from typing import List
from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

mcp = FastMCP("AgentMarketplace Server")

# ---------------------------------------------------------
# REAL RESEARCH TOOLS
# ---------------------------------------------------------
@mcp.tool()
def search_academic_sources(query: str) -> str:
    """Searches academic sources and general internet for the given query using DuckDuckGo."""
    try:
        results = DDGS().text(f"academic {query}", max_results=3)
        if not results:
            return "No academic sources found."
        
        output = "Search Results:\n"
        for r in results:
            output += f"- Title: {r.get('title')}\n  Snippet: {r.get('body')}\n  URL: {r.get('href')}\n\n"
        return output
    except Exception as e:
        return f"Error during search: {str(e)}"

@mcp.tool()
def search_news(query: str) -> str:
    """Searches recent news for the given query using DuckDuckGo."""
    try:
        results = DDGS().news(query, max_results=3)
        if not results:
            return "No news found."
            
        output = "News Results:\n"
        for r in results:
            output += f"- {r.get('date')}: {r.get('title')}\n  Snippet: {r.get('body')}\n  URL: {r.get('url')}\n\n"
        return output
    except Exception as e:
        return f"Error during news search: {str(e)}"

@mcp.tool()
def fetch_url_content(url: str) -> str:
    """Fetches and extracts text content from the provided URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text()
        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        # Drop blank lines
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit to 5000 chars to avoid overloading LLM context
        if len(text) > 5000:
            text = text[:5000] + "... [Content Truncated]"
            
        return text
    except Exception as e:
        return f"Failed to fetch URL: {str(e)}"

# ---------------------------------------------------------
# MOCKED / LOGIC TOOLS
# ---------------------------------------------------------
@mcp.tool()
def extract_key_facts(text: str) -> str:
    """Extracts key facts from the provided text."""
    return "This tool requires an LLM for extraction. Recommend using the Summarizer Agent instead."

@mcp.tool()
def rewrite_tone(text: str, tone: str) -> str:
    """Rewrites the text in a specified tone."""
    return "This tool requires an LLM for rewriting. Recommend using the Writer Agent instead."

@mcp.tool()
def seo_optimize(text: str, keywords: List[str]) -> str:
    """Optimizes text for SEO given specific keywords."""
    return "SEO Optimization requires an LLM. Recommend using the Writer Agent."

# ---------------------------------------------------------
# UTILITY TOOLS
# ---------------------------------------------------------
_context_store = {}

@mcp.tool()
def store_context(key: str, value: str) -> str:
    """Stores context data for retrieval later in the workflow."""
    _context_store[key] = value
    return f"Context saved under {key}"

@mcp.tool()
def retrieve_context(key: str) -> str:
    """Retrieves context data previously stored by key."""
    return _context_store.get(key, "Key not found")

if __name__ == "__main__":
    mcp.run()