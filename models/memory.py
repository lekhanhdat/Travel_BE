# models/memory.py - Pydantic models for user memory management

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of user memories"""
    PREFERENCE = "preference"
    INTEREST = "interest"
    VISITED = "visited"
    DISLIKE = "dislike"
    CONTEXT = "context"


class UserMemory(BaseModel):
    """User memory entry"""
    id: Optional[int] = Field(None, description="Memory ID")
    user_id: int = Field(..., description="User ID")
    memory_type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(..., description="Memory content")
    embedding_id: Optional[int] = Field(None, description="Associated embedding ID")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class StoreMemoryRequest(BaseModel):
    """Request to store a new memory"""
    user_id: int = Field(..., description="User ID")
    memory_type: MemoryType = Field(..., description="Type of memory")
    content: str = Field(
        ...,
        description="Memory content",
        min_length=1,
        max_length=1000
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "memory_type": "preference",
                "content": "User prefers beach destinations",
                "confidence": 0.9,
                "metadata": {"source": "chat_inference"}
            }
        }


class ConversationMessage(BaseModel):
    """Single message in a conversation"""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class ConversationHistory(BaseModel):
    """Conversation history for a session"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[int] = Field(None, description="User ID")
    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="List of messages"
    )
    created_at: Optional[datetime] = Field(None, description="Session start time")
    updated_at: Optional[datetime] = Field(None, description="Last message time")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123",
                "user_id": 123,
                "messages": [
                    {
                        "role": "user",
                        "content": "What beaches are in Da Nang?",
                        "timestamp": "2024-01-15T10:30:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "Da Nang has several beautiful beaches...",
                        "timestamp": "2024-01-15T10:30:02Z"
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:02Z"
            }
        }

