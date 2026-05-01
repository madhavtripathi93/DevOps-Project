import logging
import time
from typing import List, Dict, Any, Optional
from app.agents.registry import agent_registry

logger = logging.getLogger(__name__)

class Orchestrator:
    @staticmethod
    async def run_single(agent_id: str, input_text: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        agent_instance = agent_registry.get(agent_id)
        if not agent_instance:
            logger.error(f"Agent '{agent_id}' not found in registry.")
            return {
                "agent": agent_id,
                "status": "failed",
                "output": f"Agent '{agent_id}' not found in registry.",
                "metadata": {}
            }
        
        logger.info(f"Running single agent: {agent_id}")
        start_time = time.perf_counter()
        result = await agent_instance.execute(input_text, tools=tools)
        end_time = time.perf_counter()
        
        result["latency"] = f"{end_time - start_time:.2f}s"
        return result

    @staticmethod
    async def run_workflow(agent_ids: List[str], initial_input: Dict[str, Any], tools: Optional[List[str]] = None) -> Dict[str, Any]:
        results = []
        current_input = initial_input.get("input", "")
        final_output = ""
        workflow_status = "completed"
        
        logger.info(f"Starting workflow with {len(agent_ids)} agents")

        for idx, agent_id in enumerate(agent_ids):
            logger.info(f"Step {idx + 1}: Executing {agent_id}")
            
            agent_instance = agent_registry.get(agent_id)
            if not agent_instance:
                error_msg = f"Agent '{agent_id}' not found in registry."
                logger.error(error_msg)
                results.append({
                    "agent": agent_id,
                    "status": "failed",
                    "output": error_msg,
                    "latency": "0.00s",
                    "metadata": {"error": "registry_miss", "step": idx + 1}
                })
                workflow_status = "failed"
                break
            
            try:
                start_time = time.perf_counter()
                step_result = await agent_instance.execute(current_input, tools=tools)
                end_time = time.perf_counter()
                
                step_result["latency"] = f"{end_time - start_time:.2f}s"
                results.append(step_result)
                
                if step_result["status"] == "failed":
                    logger.warning(f"Step {idx + 1} ({agent_id}) failed: {step_result['output']}")
                    workflow_status = "failed"
                    break
                
                current_input = step_result["output"]
                final_output = step_result.get("structured_output", current_input)
                
                logger.info(f"Step {idx + 1} ({agent_id}) completed successfully")
                
            except Exception as e:
                logger.exception(f"Unexpected error in step {idx + 1} ({agent_id}): {str(e)}")
                results.append({
                    "agent": agent_id,
                    "status": "failed",
                    "output": f"Internal orchestrator error: {str(e)}",
                    "latency": "0.00s",
                    "metadata": {"error": str(e), "step": idx + 1}
                })
                workflow_status = "failed"
                break
            
        logger.info(f"Workflow {workflow_status} with final output")
        
        return {
            "status": workflow_status,
            "steps": results,
            "final_output": final_output
        }

    @classmethod
    async def run_auto(cls, input_text: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        logger.info(f"Running in AUTO mode for task: {input_text}")
        
        router = agent_registry.get("router")
        router_result = await router.execute(input_text)
        
        if router_result["status"] == "failed":
            return {
                "status": "failed",
                "message": "Router could not determine workflow",
                "details": router_result.get("output")
            }
            
        determined_workflow = router_result.get("workflow", ["researcher", "writer"])
        logger.info(f"Router determined workflow: {determined_workflow}")
        
        return await cls.run_workflow(determined_workflow, {"input": input_text}, tools=tools)
