from app.agents.base import BaseAgent
from app.config import settings
from typing import List, Dict, Any
import json

# Use the global model if set, otherwise fallback to agent-specific model
MODEL_NAME = settings.MAIN_MODEL or "llama3.2:3b"

class RouterAgent(BaseAgent):
    def __init__(self, model=MODEL_NAME):
        super().__init__("RouterAgent", model)

    def generate_prompt(self, input_text: str) -> str:
        return f"""
        Given the user task, decide which agents to use from the following list:
        - researcher: for gathering information and detailed research
        - summarizer: for condensing long content into key points
        - writer: for generating structured articles or formatted posts

        Rules:
        1. Return ONLY a JSON array of agent names in the order they should execute.
        2. Example: ["researcher", "summarizer", "writer"]
        3. Only use agents from the list above.
        4. If a task is simple, you can use just one or two agents.

        Task: {input_text}
        Response:
        """

    async def execute(self, input_text: str) -> Dict[str, Any]:
        result = await super().execute(input_text)
        if result["status"] == "success":
            parsed = self.parse_json_safe(result["output"])
            if isinstance(parsed, list):
                result["workflow"] = parsed
            elif isinstance(parsed, dict) and "content" in parsed:
                agents = []
                for a in ["researcher", "summarizer", "writer"]:
                    if a in parsed["content"].lower():
                        agents.append(a)
                result["workflow"] = agents if agents else ["researcher", "writer"]
            else:
                result["workflow"] = ["researcher", "writer"] # Default fallback
        return result
