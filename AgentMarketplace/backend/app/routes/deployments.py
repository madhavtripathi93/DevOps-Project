from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database.session import SessionLocal, get_db
from app.models.base import User, AgentDeployment, Agent, SavedWorkflow, WorkflowDeployment
from app.agents.registry import agent_registry
from app.services.orchestrator import Orchestrator

router = APIRouter()

# Deployment management (Requires API Key)
@router.post("/agent/{agent_id}")
async def create_deployment(agent_id: str, request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    
    # Check if agent exists
    if agent_id != "auto" and agent_id not in agent_registry:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # Check for existing active deployment for this user/agent
    existing = db.query(AgentDeployment).filter(
        AgentDeployment.user_id == user.id,
        AgentDeployment.agent_id == agent_id,
        AgentDeployment.is_active == 1
    ).first()
    
    if existing:
        return {"slug": existing.slug, "message": "Deployment already exists."}
        
    new_deployment = AgentDeployment(
        slug=AgentDeployment.generate_slug(),
        user_id=user.id,
        agent_id=agent_id
    )
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)
    
    return {"slug": new_deployment.slug, "message": "Deployment created successfully."}

@router.post("/workflow/{workflow_id}")
async def create_workflow_deployment(workflow_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    
    workflow = db.query(SavedWorkflow).filter(SavedWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    existing = db.query(WorkflowDeployment).filter(
        WorkflowDeployment.user_id == user.id,
        WorkflowDeployment.workflow_id == workflow_id,
        WorkflowDeployment.is_active == 1
    ).first()
    
    if existing:
        return {"slug": existing.slug, "message": "Deployment already exists."}
        
    new_deployment = WorkflowDeployment(
        slug=WorkflowDeployment.generate_slug(),
        user_id=user.id,
        workflow_id=workflow_id
    )
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)
    
    return {"slug": new_deployment.slug, "message": "Deployment created successfully."}

# Public execution (No API Key Required)
@router.get("/public/agent/{slug}")
async def get_public_agent(slug: str, db: Session = Depends(get_db)):
    deploy = db.query(AgentDeployment).filter(
        AgentDeployment.slug == slug,
        AgentDeployment.is_active == 1
    ).first()
    
    if not deploy:
        raise HTTPException(status_code=404, detail="Deployment link is invalid or expired.")
        
    # Get agent info from DB metadata
    agent_db = db.query(Agent).filter(Agent.agent_id == deploy.agent_id).first()
    if not agent_db:
         raise HTTPException(status_code=404, detail="Underlying agent metadata not found.")
         
    return {
        "name": agent_db.name,
        "description": agent_db.description,
        "agent_id": deploy.agent_id,
        "input_type": agent_db.input_type,
        "output_type": agent_db.output_type
    }

@router.get("/public/workflow/{slug}")
async def get_public_workflow(slug: str, db: Session = Depends(get_db)):
    deploy = db.query(WorkflowDeployment).filter(
        WorkflowDeployment.slug == slug,
        WorkflowDeployment.is_active == 1
    ).first()
    
    if not deploy:
        raise HTTPException(status_code=404, detail="Deployment link is invalid or expired.")
        
    workflow = db.query(SavedWorkflow).filter(SavedWorkflow.id == deploy.workflow_id).first()
    if not workflow:
         raise HTTPException(status_code=404, detail="Underlying workflow not found.")
         
    return {
        "name": workflow.name,
        "description": f"Automated workflow with {len(workflow.steps)} steps.",
        "steps": workflow.steps,
        "type": "workflow"
    }

@router.post("/public/agent/{slug}/run")
async def run_public_agent(slug: str, data: Dict[str, Any], db: Session = Depends(get_db)):
    deploy = db.query(AgentDeployment).filter(
        AgentDeployment.slug == slug,
        AgentDeployment.is_active == 1
    ).first()
    
    if not deploy:
        raise HTTPException(status_code=404, detail="Deployment link is invalid or expired.")
        
    # Execute based on agent type
    task_input = data.get("input", "")
    
    if deploy.agent_id == "router":
        # Public A2A Run
        return await Orchestrator.run_auto(task_input)
    else:
        # Standard Single Agent Run
        return await Orchestrator.run_single(deploy.agent_id, task_input)

@router.post("/public/workflow/{slug}/run")
async def run_public_workflow(slug: str, data: Dict[str, Any], db: Session = Depends(get_db)):
    deploy = db.query(WorkflowDeployment).filter(
        WorkflowDeployment.slug == slug,
        WorkflowDeployment.is_active == 1
    ).first()
    
    if not deploy:
        raise HTTPException(status_code=404, detail="Deployment link is invalid or expired.")
        
    workflow = db.query(SavedWorkflow).filter(SavedWorkflow.id == deploy.workflow_id).first()
    if not workflow:
         raise HTTPException(status_code=404, detail="Underlying workflow not found.")
         
    task_input = data.get("input", "")
    return await Orchestrator.run_multi(workflow.steps, task_input)
