import httpx
import os
import logging
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def health_check(response: Response, db: Session = Depends(get_db)):
    """
    Comprehensive health check verifying Database and Ollama connectivity.
    Returns 503 if any critical service is down.
    """
    health_status = {
        "status": "healthy",
        "services": {
            "database": {"status": "unknown"},
            "ollama": {"status": "unknown"}
        },
        "cache": {
            "size": 0
        }
    }
    
    is_healthy = True

    # 1. Check Database
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"]["status"] = "connected"
    except Exception as e:
        logger.error(f"Health check failed for Database: {str(e)}")
        health_status["services"]["database"]["status"] = "error"
        health_status["services"]["database"]["message"] = str(e)
        is_healthy = False

    # 2. Check Ollama (Optional)
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ollama_res = await client.get(f"{ollama_url}/api/tags")
            if ollama_res.status_code == 200:
                health_status["services"]["ollama"]["status"] = "connected"
            else:
                health_status["services"]["ollama"]["status"] = f"error: {ollama_res.status_code}"
    except Exception as e:
        logger.error(f"Health check failed for Ollama: {str(e)}")
        health_status["services"]["ollama"]["status"] = "offline (optional)"
        health_status["services"]["ollama"]["message"] = "Ollama is not running. AI features will be disabled."

    if not is_healthy:
        health_status["status"] = "unhealthy"
        response.status_code = 503

    return health_status
