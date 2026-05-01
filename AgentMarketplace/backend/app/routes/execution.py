from fastapi import APIRouter, Depends, Query, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.base import AgentOwnership
from app.services.orchestrator import Orchestrator
from app.agents.registry import agent_registry

router = APIRouter()

class ExecutionRequest(BaseModel):
    mode: str = Field("manual", description="'manual' or 'auto'")
    agent_id: Optional[str] = None
    agent_ids: Optional[List[str]] = None
    input: str = Field(..., description="User input task")
    tools: Optional[List[str]] = None # List of tool names

async def check_ownership(user_id: int, agent_ids: List[str], db: Session):
    for aid in agent_ids:
        own = db.query(AgentOwnership).filter(
            AgentOwnership.user_id == user_id,
            AgentOwnership.agent_id == aid
        ).first()
        if not own:
            raise HTTPException(
                status_code=403, 
                detail=f"You do not own agent '{aid}'. Please acquire it from the marketplace first."
            )

@router.post("/")
async def execute(request: Request, exec_req: ExecutionRequest, db: Session = Depends(get_db)):
    user = request.state.user
    
    if exec_req.mode == "auto":
        # For auto mode, we might allow it if they own the 'router' or just let it run?
        # Let's say auto mode is a premium feature or requires ownership of 'router'
        await check_ownership(user.id, ["router"], db)
        return await Orchestrator.run_auto(exec_req.input, tools=exec_req.tools)
    
    # Manual mode: single or multiple agents
    if exec_req.agent_ids:
        await check_ownership(user.id, exec_req.agent_ids, db)
        return await Orchestrator.run_workflow(exec_req.agent_ids, {"input": exec_req.input}, tools=exec_req.tools)
    elif exec_req.agent_id:
        await check_ownership(user.id, [exec_req.agent_id], db)
        return await Orchestrator.run_single(exec_req.agent_id, exec_req.input, tools=exec_req.tools)
    else:
        return {"status": "failed", "message": "Specify agent_id, agent_ids, or use mode='auto'"}

@router.post("/suggest")
async def suggest_workflow(request: Request, data: Dict[str, Any], db: Session = Depends(get_db)):
    user = request.state.user
    await check_ownership(user.id, ["router"], db)
    
    router_agent = agent_registry.get("router")
    result = await router_agent.execute(data.get("input", ""))
    if result["status"] == "success":
        return {"workflow": result.get("workflow", ["researcher", "writer"])}
    else:
        return {"status": "failed", "message": "AI Router could not determine a workflow."}

# Backward compatibility routes
@router.post("/agent/run")
async def run_single(request: Request, data: Dict[str, Any], db: Session = Depends(get_db)):
    user = request.state.user
    await check_ownership(user.id, [data.get("agent_id")], db)
    return await Orchestrator.run_single(data["agent_id"], data["input"])

@router.post("/workflow/run")
async def run_workflow(request: Request, data: Dict[str, Any], db: Session = Depends(get_db)):
    user = request.state.user
    await check_ownership(user.id, data.get("agent_ids", []), db)
    return await Orchestrator.run_workflow(data["agent_ids"], {"input": data["input"]})
