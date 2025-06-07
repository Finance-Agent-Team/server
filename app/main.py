from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.services.agent_service import AgentService
from app.models.messages import AgentMessage
from app.api.chat import router as chat_router
from app.api.stock_analysis import router as stock_analysis_router

app = FastAPI(
    title="Agent Orchestration API",
    description="Enhanced API with PydanticAI Graph-based Stock Analysis",
    version="2.0.0"
)

# Include the stock analysis router
app.include_router(stock_analysis_router)

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
    return {
        "message": "Welcome to the Enhanced Agent Orchestration API",
        "features": [
            "Traditional HTTP-based agent orchestration",
            "PydanticAI Graph-based stock analysis with MCP",
            "Interactive workflow visualization",
            "Comprehensive financial analysis pipeline"
        ],
        "endpoints": {
            "stock_analysis": "/stock-analysis",
            "docs": "/docs",
            "health": "/stock-analysis/health"
        }
    }


@app.get("/test-workflow")
async def test_pydantic_ai_workflow():
    """Test the PydanticAI stock analysis workflow"""
    
    try:
        from app.agents.pydantic_ai_stock_analyst import PydanticAIStockAnalyst, UserProfile
        
        # Create analyst instance
        analyst = PydanticAIStockAnalyst()
        
        # Generate workflow diagram
        diagram = analyst.generate_mermaid_diagram()
        
        # Create test user profile
        user_profile = UserProfile(
            name="Test User",
            risk_tolerance="moderate",
            investment_horizon="medium"
        )
        
        return {
            "success": True,
            "message": "PydanticAI workflow test successful",
            "workflow_diagram": diagram,
            "test_profile": user_profile.model_dump(),
            "available_endpoints": [
                "/stock-analysis/analyze",
                "/stock-analysis/workflow-diagram", 
                "/stock-analysis/workflow-steps/{symbol}",
                "/stock-analysis/health"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"PydanticAI workflow test failed: {str(e)}",
            "suggestion": "Check that all dependencies are installed: pip install pydantic-ai-slim[anthropic,mcp] pydantic-graph"
        }


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


# Health check for the entire application
@app.get("/health")
async def health_check():
    """Overall health check for the application"""
    
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Will be updated by actual datetime
        "services": {
            "fastapi": "healthy",
            "agent_service": "healthy"
        }
    }
    
    # Test PydanticAI workflow
    try:
        from app.agents.pydantic_ai_stock_analyst import PydanticAIStockAnalyst
        analyst = PydanticAIStockAnalyst()
        analyst.generate_mermaid_diagram()  # Simple test
        health_status["services"]["pydantic_ai_stock_analyst"] = "healthy"
    except Exception as e:
        health_status["services"]["pydantic_ai_stock_analyst"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)