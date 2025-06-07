from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
import uuid

class MessageType(str, Enum):
    QUERY = "query"
    RESPONSE = "response"
    ANALYSIS = "analysis"
    ACTION = "action"
    ERROR = "error"

class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    
class AgentNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_type: str
    properties: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class AgentEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    edge_type: str
    properties: Optional[Dict[str, Any]] = None

class AgentGraph(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nodes: List[AgentNode] = []
    edges: List[AgentEdge] = []
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    message: Optional[AgentMessage] = None
    graph: Optional[AgentGraph] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)