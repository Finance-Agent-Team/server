from typing import Dict, List, Any, Optional
import httpx
from app.models.messages import AgentMessage, AgentGraph, AgentNode, AgentEdge, AgentResponse

class AgentService:
    def __init__(self):
        self.agents: Dict[str, str] = {}  # agent_id -> endpoint_url
        self.graph = AgentGraph(nodes=[], edges=[])
        
    def register_agent(self, agent_id: str, endpoint: str, name: str, description: str, capabilities: List[str]) -> None:
        """Register an agent with the service"""
        self.agents[agent_id] = endpoint
        
        # Add to graph
        node = AgentNode(
            id=agent_id,
            name=name,
            description=description,
            capabilities=capabilities
        )
        self.graph.nodes.append(node)
        
    def connect_agents(self, source_id: str, target_id: str, relationship: str) -> None:
        """Create a connection between two agents"""
        if source_id not in self.agents or target_id not in self.agents:
            raise ValueError("Both source and target agents must be registered")
            
        edge = AgentEdge(
            source=source_id,
            target=target_id,
            relationship=relationship
        )
        self.graph.edges.append(edge)
        
    async def send_message(self, agent_id: str, message: AgentMessage) -> AgentResponse:
        """Send a message to an agent and get the response"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} is not registered")
            
        endpoint = self.agents[agent_id]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=message.model_dump(),
                timeout=60.0  # Adjust timeout as needed
            )
            
            if response.status_code != 200:
                raise Exception(f"Error from agent {agent_id}: {response.text}")
                
            return AgentResponse(
                request_id=message.id,
                message=AgentMessage(**response.json()),
                graph=self.graph
            )
        
    def get_graph(self) -> AgentGraph:
        """Return the current agent graph"""
        return self.graph
    

    async def orchestrate(self, start_agent_id: str, message: AgentMessage, path: List[str]) -> List[AgentResponse]:
        """Orchestrate a message through a path of agents"""
        responses = []
        current_message = message
        
        for agent_id in [start_agent_id] + path:
            response = await self.send_message(agent_id, current_message)
            responses.append(response)
            if response.message:  # Use response message as input to next agent
                current_message = response.message
                
        return responses

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
    
    # Create a test message
    test_message = AgentMessage(
        content="This is a test message",
        metadata={"source": "test_script"}
    )
    
    # Test the orchestration
    try:
        responses = await service.orchestrate("agent1", test_message, ["agent2"])
        print("Activation successful!")
        print(f"Received {len(responses)} responses")
        for i, response in enumerate(responses):
            print(f"Response {i+1}: {response.message.content}")
        return True
    except Exception as e:
        print(f"Activation failed: {str(e)}")
        return False