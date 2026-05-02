import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.session import engine, SessionLocal
from app.models.base import Base
from app.database.seed import seed_agents, seed_tools
from app.routes import auth, agents, execution, health, workflows, deployments, tools
from app.middleware.auth import api_key_middleware
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_db():
    try:
        logger.info("Initializing database and tables...")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_agents(db)
            seed_tools(db)
            logger.info("Database, agents, and tools initialized successfully.")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")

init_db()

app = FastAPI(title="Agent Marketplace API")

# Expose /metrics endpoint for Prometheus
Instrumentator().instrument(app).expose(app)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred. Please check logs."},
    )

origins = settings.ALLOWED_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(api_key_middleware)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(execution.router, prefix="/run", tags=["execution"])
app.include_router(workflows.router, prefix="/workflow", tags=["workflows"])
app.include_router(deployments.router, prefix="/deploy", tags=["deployments"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(health.router, prefix="/health", tags=["health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
