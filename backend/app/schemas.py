# app/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageCreate(BaseModel):
    session_id: int
    role: str = "user"
    content: str

class MessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
    escalated: bool
    answered: bool

    # pydantic v2 compatibility: allow reading attributes from ORM objects
    model_config = {"from_attributes": True}

class SessionCreate(BaseModel):
    user_id: Optional[str] = None
    # matches models.Session.meta_json
    meta_json: Optional[str] = None

class SessionOut(BaseModel):
    id: int
    user_id: Optional[str]
    created_at: datetime
    last_active: datetime
    meta_json: Optional[str]

    model_config = {"from_attributes": True}

class ChatResponse(BaseModel):
    reply: str
    escalate: bool = False
    reason: Optional[str] = None
