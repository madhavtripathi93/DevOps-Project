from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio
import logging
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

class BaseTool(ABC):
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], timeout: float = 3.0):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.timeout = timeout

    @abstractmethod
    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal tool logic execution."""
        pass

    async def execute(self, input_data: Dict[str, Any], timeout: float = None) -> Dict[str, Any]:
        """Safe execution wrapper with validation and timeout."""
        exec_timeout = timeout or self.timeout
        try:
            # 1. Validate input schema
            validate(instance=input_data, schema=self.input_schema)
            
            # 2. Execute with timeout
            result = await asyncio.wait_for(self._run(input_data), timeout=exec_timeout)
            return result
            
        except ValidationError as e:
            logger.error(f"Validation error for tool '{self.name}': {e.message}")
            return {"status": "failed", "error": f"Invalid input: {e.message}"}
        except asyncio.TimeoutError:
            logger.error(f"Timeout error for tool '{self.name}' (limit: {exec_timeout}s)")
            return {"status": "failed", "error": f"Execution timed out after {exec_timeout}s"}
        except Exception as e:
            logger.exception(f"Unexpected error in tool '{self.name}': {str(e)}")
            return {"status": "failed", "error": f"Internal error: {str(e)}"}

    def to_json(self) -> Dict[str, Any]:
        """Return a representation of the tool for LLM ingestion."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }
