from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.services.agent_service import AgentService
from app.models.messages import AgentMessage
from app.api.chat import router as chat_router

app = FastAPI(title="Agent Orchestration API")

# Add CORS middleware
origins = [
    "http://localhost:3000",  # React default port
    "http://localhost:5173",  # Vite default port
    "http://localhost:8080",  # Common development port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include the chat router
app.include_router(chat_router)

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
            "responses": [{"content": r.message.content if r.message else "No content"} for r in responses]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)