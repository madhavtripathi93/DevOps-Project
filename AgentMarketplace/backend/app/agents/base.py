from abc import ABC, abstractmethod
import sys
import httpx
import os
import time
import json
import re
import asyncio
from typing import Dict, Any, Optional, List, Set
from app.config import settings
from loguru import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure loguru
logger.add("backend.log", rotation="500 MB", level="INFO")

class BaseAgent(ABC):
    # Simple in-memory cache
    _cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, name: str, model: str = "gemma4:e4b"):
        self.name = name
        self.model = settings.LLM_MODEL_OVERRIDE if settings.LLM_MODEL_OVERRIDE else model
        self.timeout = httpx.Timeout(300.0, connect=20.0) # 300s total, 20s connect
        self.confidence_threshold = 0.5
        self.max_tool_budget = 5 # Production rate limit per request

    @abstractmethod
    def generate_prompt(self, input_text: str) -> str:
        pass

    def extract_json_calls(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON objects from LLM text output."""
        calls = []
        
        # Strip markdown formatting
        md_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if md_match:
            text = md_match.group(1)

        # Attempt to parse as full JSON array
        if "[" in text and "]" in text:
            try:
                arr_text = text[text.find("["):text.rfind("]")+1]
                data = json.loads(arr_text)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "tool" in item and "input" in item:
                            calls.append(item)
                    if calls:
                        return calls
            except json.JSONDecodeError:
                pass

        # Fallback to regex for individual objects
        matches = re.finditer(r"(\{.*?\})", text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match.group(1))
                if "tool" in data and "input" in data:
                    calls.append(data)
            except json.JSONDecodeError:
                continue
                
        return calls

    async def execute(self, input_text: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        logger.info(f"[{self.name}] Initiating intelligent execution. Budget: {self.max_tool_budget}")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        server_py_path = os.path.join(project_root, "mcp_server", "server.py")
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_py_path],
            env={**os.environ}
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # 1. Fetch MCP Tools
                    tools_response = await session.list_tools()
                    
                    # Format for Prompt - only get what we need or everything if no filter provided
                    tool_definitions = []
                    for t in tools_response.tools:
                        if not tools or t.name in tools:
                            tool_definitions.append({
                                "name": t.name,
                                "description": t.description,
                                "schema": t.inputSchema
                            })
                    
                    # 2. Intelligent Prompt Refinement
                    system_instruction = f"""
                    You are a production-grade AI agent Optimizer. 
                    GOAL: Solve the user's task with MINIMAL tool usage.
                    
                    AVAILABLE TOOLS (via MCP):
                    {json.dumps(tool_definitions, indent=2)}
            
                    RULES:
                    1. Only use tools if strictly required for accuracy.
                    2. If you need to use tools, output ONLY a valid JSON array of tool calls. Do NOT output conversational text before or after the JSON.
                    3. Format MUST be exactly: [{{"tool": "name", "input": {{"key": "val"}}, "confidence": 0.9}}]
                    4. Check your syntax. Missing quotes or brackets will cause the system to fail.
                    5. Once you have gathered sufficient information, provide your final response in clear Markdown format. DO NOT output JSON in your final answer.
                    """
            
                    history = [{"role": "user", "content": self.generate_prompt(input_text)}]
                    if tool_definitions:
                        history.insert(0, {"role": "system", "content": system_instruction})
            
                    max_turns = 5
                    current_turn = 0
                    tool_count = 0
                    all_steps = []
                    executed_calls = set()
            
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        while current_turn < max_turns:
                            current_turn += 1
                            
                            # LLM Generation
                            llm_output = await self._call_llm(client, history)
                            
                            # 3. Parallel Tool Call Detection
                            tool_calls = self.extract_json_calls(llm_output)
                            
                            if tool_calls:
                                # 4. Rate Limiting & Safety
                                if tool_count + len(tool_calls) > self.max_tool_budget:
                                    logger.warning(f"[{self.name}] Rate limit hit. Budget exceeded.")
                                    return {
                                        "status": "failed", 
                                        "output": f"Error: Tool execution budget ({self.max_tool_budget}) exceeded for this request.",
                                        "metadata": {"error": "rate_limit_exceeded"}
                                    }
                                
                                # 5. Adaptive Confidence & Parallel Execution
                                tasks = []
                                valid_calls = []
                                
                                for call in tool_calls:
                                    tool_name = call["tool"]
                                    tool_input = call["input"]
                                    confidence = call.get("confidence", 1.0)
                                    
                                    if confidence < self.confidence_threshold:
                                        logger.info(f"[{self.name}] Skipping low-confidence call to {tool_name} ({confidence})")
                                        continue
                                        
                                    call_hash = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
                                    if call_hash in executed_calls:
                                        logger.error(f"[{self.name}] Loop detected for {tool_name}. Aborting turn.")
                                        break
                                    
                                    executed_calls.add(call_hash)
                                    
                                    # Use MCP ClientSession to call the tool
                                    tasks.append(session.call_tool(tool_name, tool_input))
                                    valid_calls.append(call)
                                
                                if tasks:
                                    logger.info(f"[{self.name}] Executing {len(tasks)} MCP tools in PARALLEL")
                                    t_start = time.perf_counter()
                                    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
                                    t_duration = time.perf_counter() - t_start
                                    
                                    # Handle CallToolResult which contains .content[] list
                                    results = []
                                    for res in raw_results:
                                        if isinstance(res, Exception):
                                            results.append(f"Error: {str(res)}")
                                        else:
                                            try:
                                                text_output = " ".join([c.text for c in res.content if c.type == "text"])
                                                results.append(text_output)
                                            except Exception as e:
                                                results.append(f"Failed to parse tool result: {str(res)}")
                                                
                                    tool_count += len(tasks)
                                    
                                    # 6. Adaptive Failure Context
                                    turn_results = []
                                    for call, res in zip(valid_calls, results):
                                        step = {"tool": call["tool"], "input": call["input"], "output": res, "duration": f"{t_duration:.2f}s"}
                                        all_steps.append(step)
                                        turn_results.append(step)
                                    
                                    history.append({"role": "assistant", "content": llm_output})
                                    history.append({"role": "user", "content": f"Parallel MCP Execution Results: {json.dumps(turn_results)}"})
                                    continue # Next reasoning turn
                                
                            # Final Answer Path
                            duration = time.perf_counter() - start_time
                            logger.success(f"[{self.name}] Mission accomplished in {duration:.2f}s ({tool_count} tools)")
                            
                            return {
                                "agent": self.name,
                                "status": "success",
                                "input": input_text,
                                "output": llm_output,
                                "steps": all_steps,
                                "metadata": {
                                    "model": self.model,
                                    "turns": current_turn,
                                    "tool_calls": tool_count,
                                    "total_duration": f"{duration:.2f}s"
                                }
                            }

                        return {"status": "failed", "output": "Max reasoning cycles reached."}

        except Exception as e:
            logger.exception(f"[{self.name}] Orchestration failure: {str(e)}")
            return {"status": "failed", "output": f"Recovery failed: {str(e)}"}

    async def _call_llm(self, client: httpx.AsyncClient, history: List[Dict[str, str]]) -> str:
        """Optimized LLM Caller."""
        provider = settings.LLM_PROVIDER
        if provider == "ollama":
            full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in history])
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": self.model, "prompt": full_prompt, "stream": False}
            )
            response.raise_for_status()
            return response.json().get("response", "")
        
        elif provider in ["groq", "openai"]:
            url = "https://api.groq.com/openai/v1/chat/completions" if provider == "groq" else "https://api.openai.com/v1/chat/completions"
            target_model = self.model
            if provider == "groq" and self.model == "llama3.2:3b":
                target_model = "llama-3.1-8b-instant"
            elif provider == "openai" and self.model == "llama3.2:3b":
                target_model = "gpt-3.5-turbo"

            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                json={"model": target_model, "messages": history, "temperature": 0.1}
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        
        raise Exception(f"Unsupported provider: {provider}")