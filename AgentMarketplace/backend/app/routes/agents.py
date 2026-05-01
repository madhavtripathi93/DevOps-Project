from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.base import Agent, AgentOwnership

router = APIRouter()

@router.get("/")
def get_agents(db: Session = Depends(get_db)):
    return db.query(Agent).all()

@router.get("/my")
def get_my_agents(request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    owned = db.query(AgentOwnership).filter(AgentOwnership.user_id == user.id).all()
    owned_ids = [o.agent_id for o in owned]
    return db.query(Agent).filter(Agent.agent_id.in_(owned_ids)).all()

@router.post("/acquire/{agent_id}")
def acquire_agent(agent_id: str, request: Request, db: Session = Depends(get_db)):
    user = request.state.user
    
    # Check if agent exists
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # Check if already owned
    existing = db.query(AgentOwnership).filter(
        AgentOwnership.user_id == user.id,
        AgentOwnership.agent_id == agent_id
    ).first()
    
    if existing:
        return {"message": "Agent already in library."}
        
    new_own = AgentOwnership(user_id=user.id, agent_id=agent_id)
    db.add(new_own)
    db.commit()
    return {"message": f"Agent {agent.name} added to your library."}
