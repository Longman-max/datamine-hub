from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AgentBase(BaseModel):
    id: str

class AgentCreateResponse(AgentBase):
    api_key: str
    created_at: datetime

class DataNodeResponse(BaseModel):
    hash: str
    agent_id: str
    storage_path: str
    metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

class LineageResponse(BaseModel):
    nodes: List[DataNodeResponse]
    edges: List[Dict[str, str]]

class PostCreate(BaseModel):
    content: str

class PostResponse(BaseModel):
    id: int
    channel_name: str
    agent_id: str
    content: str
    created_at: datetime

class JobSpawnRequest(BaseModel):
    role: str
    target_url: str
