from sqlalchemy.orm import Session
from app.models.base import Agent, Tool

def seed_agents(db: Session):
    default_agents = [
        {
            "agent_id": "router",
            "name": "AI Orchestrator",
            "description": "Automatically selects and sequences agents to solve complex tasks.",
            "input_type": "high-level-task",
            "output_type": "orchestrated_result",
            "capabilities": ["Dynamic Agent Selection", "Multi-step Orchestration", "Output Synthesis"],
            "skills": ["Strategic Planning", "Agent Management", "Complex Problem Solving"]
        },
        {
            "agent_id": "researcher",
            "name": "Researcher Agent",
            "description": "Generates detailed bullet points with headings about a topic.",
            "input_type": "topic",
            "output_type": "detailed_notes",
            "capabilities": ["Deep Fact Extraction", "Structural Note-taking", "Multi-source Synthesis"],
            "skills": ["Information Retrieval", "Technical Writing", "Data Organization"]
        },
        {
            "agent_id": "summarizer",
            "name": "Summarizer Agent",
            "description": "Summarizes content concisely.",
            "input_type": "content",
            "output_type": "summary",
            "capabilities": ["Abstractive Summarization", "Key Point Extraction", "Context Retention"],
            "skills": ["NLP Analysis", "Conciseness", "Core Message Identification"]
        },
        {
            "agent_id": "writer",
            "name": "Writer Agent",
            "description": "Converts summary into a structured article with headings and paragraphs.",
            "input_type": "summary",
            "output_type": "article",
            "capabilities": ["Narrative Flow Design", "Tone Adaptation", "Structural Refinement"],
            "skills": ["Creative Writing", "Content Strategy", "Editorial Planning"]
        }
    ]

    for agent_data in default_agents:
        existing = db.query(Agent).filter(Agent.agent_id == agent_data["agent_id"]).first()
        if not existing:
            new_agent = Agent(**agent_data)
            db.add(new_agent)
        else:
            # Update existing with new fields
            existing.capabilities = agent_data["capabilities"]
            existing.skills = agent_data["skills"]
    
    db.commit()
    print("Agents seeded successfully with rich metadata.")

def seed_tools(db: Session):
    from app.tools.registry import tool_registry
    
    # Get tools from the in-memory registry
    tools = tool_registry.list_tools()
    
    for tool_instance in tools:
        existing = db.query(Tool).filter(Tool.name == tool_instance.name).first()
        if not existing:
            new_tool = Tool(
                name=tool_instance.name,
                description=tool_instance.description,
                input_schema=tool_instance.input_schema,
                owner_id=1, # Default to admin/system
                is_public=1
            )
            db.add(new_tool)
            print(f"Seeded tool: {tool_instance.name}")
        else:
            # Sync metadata for existing tool
            existing.description = tool_instance.description
            existing.input_schema = tool_instance.input_schema
            print(f"Synchronized tool: {tool_instance.name}")
    
    db.commit()
    print("Tools seeded successfully.")
