from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database.session import get_db
from app.models.base import Tool, ToolOwnership
from app.tools.registry import tool_registry

router = APIRouter()

@router.post("/register")
async def register_tool(request: Request, data: Dict[str, Any], db: Session = Depends(get_db)):
    user = request.state.user
    
    name = data.get("name")
    description = data.get("description")
    input_schema = data.get("input_schema")
    
    if not name or not description or not input_schema:
        raise HTTPException(status_code=400, detail="Missing required tool fields.")
        
    # Check if tool exists in DB
    existing = db.query(Tool).filter(Tool.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tool name already registered.")
        
    new_tool = Tool(
        name=name,
        description=description,
        input_schema=input_schema,
        owner_id=user.id,
        is_public=data.get("is_public", 1)
    )
    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)
    
    return {"message": "Tool registered successfully", "id": new_tool.id}

@router.get("/")
async def list_marketplace_tools(db: Session = Depends(get_db)):
    """List all public tools in the marketplace."""
    tools = db.query(Tool).filter(Tool.is_public == 1).all()
    return [{
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "input_schema": t.input_schema,
        "is_public": t.is_public
    } for t in tools]

@router.get("/my")
async def list_my_tools(request: Request, db: Session = Depends(get_db)):
    """List tools owned or acquired by the user."""
    user = request.state.user
    
    # Tools created by user
    owned_tools = db.query(Tool).filter(Tool.owner_id == user.id).all()
    
    # Tools acquired from marketplace
    acquired_ids = db.query(ToolOwnership.tool_id).filter(ToolOwnership.user_id == user.id).all()
    acquired_ids = [r[0] for r in acquired_ids]
    acquired_tools = db.query(Tool).filter(Tool.id.in_(acquired_ids)).all()
    
    # Combine (deduplicate)
    all_tools = list(set(owned_tools + acquired_tools))
    
    return [{
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "input_schema": t.input_schema
    } for t in all_tools]

@router.post("/acquire/{tool_id}")
async def acquire_tool(request: Request, tool_id: int, db: Session = Depends(get_db)):
    """Add a marketplace tool to the user's library."""
    user = request.state.user
    
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
        
    if tool.owner_id == user.id:
        return {"message": "You already own this tool"}
        
    existing = db.query(ToolOwnership).filter(
        ToolOwnership.user_id == user.id,
        ToolOwnership.tool_id == tool_id
    ).first()
    
    if existing:
        return {"message": "Tool already in your library"}
        
    ownership = ToolOwnership(user_id=user.id, tool_id=tool_id)
    db.add(ownership)
    db.commit()
    
    return {"message": "Tool acquired successfully"}

@router.get("/definitions")
async def get_tool_definitions():
    """Return in-memory tool definitions from registry."""
    return [t.to_json() for t in tool_registry.list_tools()]

@router.post("/execute/{name}")
async def execute_tool_direct(request: Request, name: str, input_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Execute a tool directly with ownership verification."""
    user = request.state.user
    
    # 1. Verify ownership/access
    tool_db = db.query(Tool).filter(Tool.name == name).first()
    if not tool_db:
        raise HTTPException(status_code=404, detail="Tool not found in database")
        
    is_owner = tool_db.owner_id == user.id
    is_acquired = db.query(ToolOwnership).filter(
        ToolOwnership.user_id == user.id,
        ToolOwnership.tool_id == tool_db.id
    ).first() is not None
    
    if not (is_owner or is_acquired or tool_db.is_public):
        raise HTTPException(status_code=403, detail="You do not have access to this tool")
        
    # 2. Get tool from registry
    tool_instance = tool_registry.get(name)
    if not tool_instance:
        raise HTTPException(status_code=404, detail="Tool implementation not found in registry")
        
    # 3. Execute
    result = await tool_instance.execute(input_data)
    
    return {
        "tool": name,
        "input": input_data,
        "result": result,
        "status": "success" if result.get("status") != "failed" else "failed"
    }
