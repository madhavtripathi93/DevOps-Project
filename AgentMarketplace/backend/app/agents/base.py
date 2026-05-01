import os
import sys
import json
import time
import re
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypedDict
import httpx

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.graph import StateGraph, END

from app.config import settings
from loguru import logger

logger.add("backend.log", rotation="500 MB", level="INFO")

class AgentState(TypedDict):
    input_text: str
    mcp_session: Any
    available_tools: List[Dict[str, Any]]
    history: List[Dict[str, str]]
    all_steps: List[Dict[str, Any]]
    executed_calls: set
    tool_count: int
    max_tool_budget: int
    confidence_threshold: float
    final_output: str
    status: str
    error_message: str

class BaseAgent(ABC):
    def __init__(self, name: str, model: str = "llama3.2:3b"):
        self.name = name
        # Prioritize main model, then specific model
        self.model = settings.MAIN_MODEL or model
        self.timeout = httpx.Timeout(300.0, connect=20.0)
        self.confidence_threshold = 0.5
        self.max_tool_budget = 5

    @abstractmethod
    def generate_prompt(self, input_text: str) -> str:
        pass

    def extract_json_calls(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON objects from LLM text output."""
        calls = []
        
        # 1. Try to find markdown block
        md_match = re.search(r"```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```", text, re.DOTALL)
        content = md_match.group(1) if md_match else text

        # 2. Try to find a JSON array
        array_match = re.search(r"(\[\s*\{.*?\}\s*\])", content, re.DOTALL)
        if array_match:
            try:
                data = json.loads(array_match.group(1))
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "tool" in item and "input" in item:
                            calls.append(item)
                    if calls:
                        return calls
            except json.JSONDecodeError:
                pass

        # 3. Fallback to finding individual JSON objects
        matches = re.finditer(r"(\{\s*\"tool\"\s*:\s*\".*?\}\s*\})", content, re.DOTALL)
        for match in matches:
            try:
                # Basic cleanup
                clean_str = match.group(1).replace('\n', '')
                data = json.loads(clean_str)
                if "tool" in data and "input" in data:
                    calls.append(data)
            except json.JSONDecodeError:
                continue
                
        return calls

    def parse_json_safe(self, text: str) -> Any:
        try:
            return json.loads(text)
        except:
            md_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if md_match:
                try:
                    return json.loads(md_match.group(1))
                except:
                    pass
        return text

    async def _call_llm(self, history: List[Dict[str, str]]) -> str:
        """Call the configured LLM."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if not settings.MAIN_API_KEY:
                # Local LLM (Ollama)
                full_prompt = "\n".join([f"{m['role']}: {m['content']}" for m in history])
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={"model": self.model, "prompt": full_prompt, "stream": False}
                )
                response.raise_for_status()
                return response.json().get("response", "")
            
            else:
                # External API (OpenAI Compatible)
                # We default to Groq URL for fast inference if model contains llama, else OpenAI
                url = "https://api.groq.com/openai/v1/chat/completions" if "llama" in self.model.lower() or "mixtral" in self.model.lower() else "https://api.openai.com/v1/chat/completions"
                
                target_model = self.model
                if "llama3.2:3b" in self.model:
                    target_model = "llama-3.1-8b-instant" # Fast fallback for Groq

                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.MAIN_API_KEY}"},
                    json={"model": target_model, "messages": history, "temperature": 0.1}
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]

    # LangGraph Nodes
    async def llm_node(self, state: AgentState) -> AgentState:
        try:
            llm_output = await self._call_llm(state["history"])
            tool_calls = self.extract_json_calls(llm_output)
            
            if tool_calls:
                state["status"] = "tool_execution"
                state["history"].append({"role": "assistant", "content": llm_output})
            else:
                state["status"] = "success"
                state["final_output"] = llm_output
                
            return state
        except Exception as e:
            state["status"] = "failed"
            state["error_message"] = str(e)
            return state

    async def tool_node(self, state: AgentState) -> AgentState:
        llm_output = state["history"][-1]["content"]
        tool_calls = self.extract_json_calls(llm_output)
        
        if state["tool_count"] + len(tool_calls) > state["max_tool_budget"]:
            state["status"] = "failed"
            state["error_message"] = "Tool execution budget exceeded."
            return state

        tasks = []
        valid_calls = []
        
        for call in tool_calls:
            tool_name = call["tool"]
            tool_input = call["input"]
            confidence = call.get("confidence", 1.0)
            
            if confidence < state["confidence_threshold"]:
                continue
                
            call_hash = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
            if call_hash in state["executed_calls"]:
                state["status"] = "failed"
                state["error_message"] = "Infinite tool loop detected."
                return state
            
            state["executed_calls"].add(call_hash)
            tasks.append(state["mcp_session"].call_tool(tool_name, tool_input))
            valid_calls.append(call)
        
        if tasks:
            t_start = time.perf_counter()
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)
            t_duration = time.perf_counter() - t_start
            
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
                        
            state["tool_count"] += len(tasks)
            
            turn_results = []
            for call, res in zip(valid_calls, results):
                step = {"tool": call["tool"], "input": call["input"], "output": res, "duration": f"{t_duration:.2f}s"}
                state["all_steps"].append(step)
                turn_results.append(step)
            
            state["history"].append({"role": "user", "content": f"Tool Results: {json.dumps(turn_results)}"})
        
        return state

    def router(self, state: AgentState) -> str:
        if state["status"] == "failed":
            return END
        if state["status"] == "success":
            return END
        return "tool_node"

    async def execute(self, input_text: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        logger.info(f"[{self.name}] Initiating LangGraph execution.")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        server_py_path = os.path.join(project_root, "mcp_server", "server.py")
        
        server_params = StdioServerParameters(command=sys.executable, args=[server_py_path], env={**os.environ})

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Select necessary tools from MCP
                    tools_response = await session.list_tools()
                    tool_definitions = []
                    for t in tools_response.tools:
                        if not tools or t.name in tools:
                            tool_definitions.append({
                                "name": t.name,
                                "description": t.description,
                                "schema": t.inputSchema
                            })
                    
                    system_instruction = f"""
                    You are a production-grade AI agent. Solve the user's task.
                    
                    AVAILABLE TOOLS:
                    {json.dumps(tool_definitions, indent=2)}
            
                    RULES:
                    1. Use tools only if required.
                    2. To use tools, output ONLY a JSON array: [{{"tool": "name", "input": {{"key": "val"}}, "confidence": 0.9}}]
                    3. Do not output text before or after the JSON tool call.
                    4. Once you have enough info, provide your final response in clear text.
                    """
            
                    history = [{"role": "system", "content": system_instruction}, {"role": "user", "content": self.generate_prompt(input_text)}]
            
                    # Initialize State
                    initial_state = AgentState(
                        input_text=input_text,
                        mcp_session=session,
                        available_tools=tool_definitions,
                        history=history,
                        all_steps=[],
                        executed_calls=set(),
                        tool_count=0,
                        max_tool_budget=self.max_tool_budget,
                        confidence_threshold=self.confidence_threshold,
                        final_output="",
                        status="running",
                        error_message=""
                    )

                    # Build LangGraph
                    workflow = StateGraph(AgentState)
                    workflow.add_node("llm_node", self.llm_node)
                    workflow.add_node("tool_node", self.tool_node)
                    
                    workflow.set_entry_point("llm_node")
                    workflow.add_conditional_edges("llm_node", self.router)
                    workflow.add_edge("tool_node", "llm_node")
                    
                    app = workflow.compile()
                    
                    # Execute Graph
                    final_state = await app.ainvoke(initial_state)
                    
                    duration = time.perf_counter() - start_time
                    
                    if final_state["status"] == "failed":
                        return {"status": "failed", "output": final_state["error_message"]}
                        
                    return {
                        "agent": self.name,
                        "status": "success",
                        "input": input_text,
                        "output": final_state["final_output"],
                        "steps": final_state["all_steps"],
                        "metadata": {
                            "model": self.model,
                            "tool_calls": final_state["tool_count"],
                            "total_duration": f"{duration:.2f}s"
                        }
                    }

        except Exception as e:
            logger.exception(f"[{self.name}] Orchestration failure: {str(e)}")
            return {"status": "failed", "output": f"Failure: {str(e)}"}