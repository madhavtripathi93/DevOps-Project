from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from app.database.session import Base
import secrets

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    api_key = Column(String(64), unique=True, index=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_api_key():
        return f"ag-{secrets.token_hex(20)}"

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    description = Column(String(255))
    input_type = Column(String(50))
    output_type = Column(String(50))
    agent_id = Column(String(50), unique=True) # e.g. 'researcher'
    capabilities = Column(JSON) # List of strings
    skills = Column(JSON) # List of strings

class SavedWorkflow(Base):
    __tablename__ = "saved_workflows"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    name = Column(String(100))
    steps = Column(JSON) # List of agent IDs
    is_public = Column(Integer, default=0) # 1 for public in marketplace
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    workflow_type = Column(String(50)) # 'single' or 'multi'
    steps = Column(JSON) # List of step results
    status = Column(String(20)) # 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentDeployment(Base):
    __tablename__ = "agent_deployments"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, index=True)
    user_id = Column(Integer)
    agent_id = Column(String(50))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_slug():
        return secrets.token_urlsafe(12)
class WorkflowDeployment(Base):
    __tablename__ = "workflow_deployments"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, index=True)
    user_id = Column(Integer)
    workflow_id = Column(Integer)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_slug():
        return secrets.token_urlsafe(12)

class Tool(Base):
    __tablename__ = "tools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(String(255))
    input_schema = Column(JSON) # JSON Schema for validation
    owner_id = Column(Integer, index=True)
    is_public = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class A2ADeployment(Base):
    __tablename__ = "a2a_deployments"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, index=True)
    user_id = Column(Integer)
    name = Column(String(100))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_slug():
        return secrets.token_urlsafe(12)

class AgentOwnership(Base):
    __tablename__ = "agent_ownership"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    agent_id = Column(String(50), index=True)
    acquired_at = Column(DateTime, default=datetime.utcnow)

class WorkflowOwnership(Base):
    __tablename__ = "workflow_ownership"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    workflow_id = Column(Integer, index=True)
    acquired_at = Column(DateTime, default=datetime.utcnow)

class ToolOwnership(Base):
    __tablename__ = "tool_ownership"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tool_id = Column(Integer, index=True)
    acquired_at = Column(DateTime, default=datetime.utcnow)
