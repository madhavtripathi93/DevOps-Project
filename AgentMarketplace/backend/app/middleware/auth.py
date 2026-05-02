from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.models.base import User
from app.database.session import SessionLocal

async def api_key_middleware(request: Request, call_next):
    # Skip API key validation for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
        
    path = request.url.path.rstrip("/")
    if (path in ["/auth/register", "/auth/login", "/health", "/docs", "/openapi.json"] or path.startswith("/docs")):
        return await call_next(request)
    
    api_key = request.headers.get("x-api-key")
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": "Missing API Key"}
        )
    
    db = SessionLocal()
    user = db.query(User).filter(User.api_key == api_key).first()
    
    if not user:
        db.close()
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": "Invalid API Key"}
        )
    
    # Store user in request state
    request.state.user = user
    response = await call_next(request)
    db.close()
    return response
