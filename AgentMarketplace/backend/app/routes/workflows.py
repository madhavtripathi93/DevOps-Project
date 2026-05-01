from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.database.session import get_db
from app.models.base import User, SavedWorkflow, WorkflowOwnership
from app.services.orchestrator import Orchestrator
from sqlalchemy import or_

router = APIRouter()

class WorkflowSaveRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    steps: List[str]
    is_public: bool = False

@router.post("/save")
async def save_workflow(request: Request, save_req: WorkflowSaveRequest, db: Session = Depends(get_db)):
    user = request.state.user
    new_workflow = SavedWorkflow(
        user_id=user.id,
        name=save_req.name,
        steps=save_req.steps,
        is_public=1 if save_req.is_public else 0
    )
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    return {"id": new_workflow.id, "message": "Workflow saved successfully"}

@router.get("/list")
async def list_public_workflows(db: Session = Depends(get_db)):
    # Marketplace: Only public workflows
    workflows = db.query(SavedWorkflow).filter(SavedWorkflow.is_public == 1).all()
    return [{"id": w.id, "name": w.name, "steps": w.steps, "created_at": w.created_at} for w in workflows]

@router.get("/my")
async def list_my_workflows(request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    # Owned = Created by me OR Acquired by me
    owned_ids = [o.workflow_id for o in db.query(WorkflowOwnership).filter(WorkflowOwnership.user_id == user.id).all()]
    
    workflows = db.query(SavedWorkflow).filter(
        or_(
            SavedWorkflow.user_id == user.id,
            SavedWorkflow.id.in_(owned_ids) if owned_ids else False
        )
    ).all()
    return [{"id": w.id, "name": w.name, "steps": w.steps, "created_at": w.created_at} for w in workflows]

@router.post("/acquire/{id}")
async def acquire_workflow(id: int, request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    
    workflow = db.query(SavedWorkflow).filter(SavedWorkflow.id == id, SavedWorkflow.is_public == 1).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Public workflow template not found")
        
    if workflow.user_id == user.id:
        return {"message": "You already own this workflow (you created it)."}
        
    existing = db.query(WorkflowOwnership).filter(
        WorkflowOwnership.user_id == user.id,
        WorkflowOwnership.workflow_id == id
    ).first()
    
    if existing:
        return {"message": "Workflow already in library."}
        
    new_own = WorkflowOwnership(user_id=user.id, workflow_id=id)
    db.add(new_own)
    db.commit()
    return {"message": f"Workflow {workflow.name} added to your library."}

@router.post("/run/{id}")
async def run_saved_workflow(id: int, request: Request, data: Dict[str, Any], db: Session = Depends(get_db)):
    user = request.state.user
    
    # Ownership Check
    owned_ids = [o.workflow_id for o in db.query(WorkflowOwnership).filter(WorkflowOwnership.user_id == user.id).all()]
    workflow = db.query(SavedWorkflow).filter(
        SavedWorkflow.id == id,
        or_(
            SavedWorkflow.user_id == user.id,
            SavedWorkflow.id.in_(owned_ids) if owned_ids else False
        )
    ).first()
    
    if not workflow:
        raise HTTPException(status_code=403, detail="You do not have access to this workflow. Please acquire it from the marketplace first.")
    
    return await Orchestrator.run_workflow(workflow.steps, data.get("input", ""))
