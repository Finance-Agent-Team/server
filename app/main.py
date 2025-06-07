from fastapi import FastAPI
import uvicorn
from app.services.agent_service import AgentService
from app.models.messages import AgentMessage

app = FastAPI(title="Agent Orchestration API")

@app.get("/")
async def root():
    return {"message": "Welcome to my API"}


@app.get("/test-agent-activation")
async def test_agent_activation():
    # Create the agent service
    service = AgentService()
    
    # Register your agents
    service.register_agent(
        agent_id="agent1",
        endpoint="http://localhost:8001/api/agent",
        name="First Agent",
        description="Handles initial processing",
        capabilities=["text_analysis", "classification"]
    )
    
    service.register_agent(
        agent_id="agent2",
        endpoint="http://localhost:8002/api/agent",
        name="Second Agent",
        description="Processes results from first agent",
        capabilities=["summarization", "response_generation"]
    )
    
    # Connect the agents
    service.connect_agents("agent1", "agent2", "feeds_into")
    
    # Create a test message
    test_message = AgentMessage(
        content="This is a test message",
        metadata={"source": "test_api"}
    )
    
    # Test the orchestration
    try:
        responses = await service.orchestrate("agent1", test_message, ["agent2"])
        return {
            "success": True,
            "message": f"Received {len(responses)} responses",
            "responses": [{"content": r.message.content} for r in responses]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)