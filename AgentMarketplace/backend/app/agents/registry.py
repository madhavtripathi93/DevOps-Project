from app.agents.base import BaseAgent
from app.agents.router_agent import RouterAgent

class ResearcherAgent(BaseAgent):
    def __init__(self, model="gemma4:e4b"):
        super().__init__("ResearcherAgent", model)

    def generate_prompt(self, input_text: str) -> str:
        return f"Generate detailed, structured bullet points with headings about: {input_text}. Include key facts, examples, and insights."

class SummarizerAgent(BaseAgent):
    def __init__(self, model="gemma4:e4b"):
        super().__init__("SummarizerAgent", model)

    def generate_prompt(self, input_text: str) -> str:
        return f"Summarize the following content into concise, meaningful points. Preserve important details and structure: {input_text}"

class WriterAgent(BaseAgent):
    def __init__(self, model="gemma4:e4b"):
        super().__init__("WriterAgent", model)

    def generate_prompt(self, input_text: str) -> str:
        return f"""
        Write a professional article with:
        - Title
        - Introduction
        - 3 to 5 sections with headings
        - Conclusion

        Return output in JSON format:
        {{
            "title": "...",
            "sections": [
                {{"heading": "...", "content": "..."}}
            ],
            "conclusion": "..."
        }}

        Content:
        {input_text}
        """

    async def execute(self, input_text: str):
        result = await super().execute(input_text)
        if result["status"] == "success":
            parsed = self.parse_json_safe(result["output"])
            result["structured_output"] = parsed
        return result

# Registry
agent_registry = {
    "researcher": ResearcherAgent(),
    "summarizer": SummarizerAgent(),
    "writer": WriterAgent(),
    "router": RouterAgent()
}
