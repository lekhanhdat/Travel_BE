# models/chat.py - Pydantic models for RAG chat

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatSource(BaseModel):
    """Source reference for RAG response"""
    entity_id: int = Field(..., description="ID of the source entity")
    entity_type: str = Field(..., description="Type of source entity")
    title: str = Field(..., description="Title of the source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    snippet: Optional[str] = Field(None, description="Relevant text snippet")


class SuggestedAction(BaseModel):
    """Suggested follow-up action"""
    action_type: str = Field(..., description="Type of action (navigate, search, etc.)")
    label: str = Field(..., description="Display label for the action")
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Action payload data"
    )


class RAGChatRequest(BaseModel):
    """Request model for RAG-enhanced chat"""
    message: str = Field(
        ...,
        description="User message",
        min_length=1,
        max_length=2000
    )
    user_id: Optional[int] = Field(
        default=None,
        description="User ID for personalization"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )
    include_sources: bool = Field(
        default=True,
        description="Whether to include source references"
    )
    max_context_items: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of context items to retrieve"
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64 encoded image for multimodal chat"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the best beaches in Da Nang?",
                "user_id": 123,
                "session_id": "abc-123",
                "include_sources": True,
                "max_context_items": 5
            }
        }


class RAGChatResponse(BaseModel):
    """Response model for RAG-enhanced chat"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="AI-generated response")
    sources: List[ChatSource] = Field(
        default_factory=list,
        description="Source references used in response"
    )
    suggested_actions: List[SuggestedAction] = Field(
        default_factory=list,
        description="Suggested follow-up actions"
    )
    session_id: str = Field(..., description="Session ID for conversation continuity")
    tokens_used: int = Field(default=0, description="Number of tokens used")
    response_time_ms: float = Field(..., description="Response generation time in ms")
    error: Optional[str] = Field(None, description="Error message if request failed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Da Nang has several beautiful beaches...",
                "sources": [
                    {
                        "entity_id": 1,
                        "entity_type": "location",
                        "title": "My Khe Beach",
                        "relevance_score": 0.95,
                        "snippet": "My Khe Beach is one of the most beautiful..."
                    }
                ],
                "suggested_actions": [
                    {
                        "action_type": "navigate",
                        "label": "View My Khe Beach",
                        "payload": {"screen": "LocationDetail", "id": 1}
                    }
                ],
                "session_id": "abc-123",
                "tokens_used": 450,
                "response_time_ms": 1250.5
            }
        }

