# routers/memory.py - User memory management API endpoints

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models.memory import (
    UserMemory,
    MemoryType,
    StoreMemoryRequest,
    ConversationHistory,
)
from services import get_memory_service

router = APIRouter(prefix="/api/v1/memory", tags=["User Memory"])


@router.post("/store")
async def store_memory(request: StoreMemoryRequest) -> dict:
    """
    Store a user memory/preference.
    
    Memory types:
    - preference: User preferences (e.g., "prefers beach destinations")
    - interest: User interests (e.g., "interested in history")
    - visited: Places user has visited
    - dislike: Things user dislikes
    - context: Contextual information
    """
    try:
        memory_service = get_memory_service()
        
        memory_id = memory_service.store_memory(
            user_id=request.user_id,
            memory_type=request.memory_type.value,
            content=request.content,
            confidence=request.confidence,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory stored successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_memories(
    user_id: int,
    memory_type: Optional[MemoryType] = None,
    limit: int = Query(default=10, ge=1, le=50)
) -> dict:
    """Get memories for a specific user"""
    try:
        memory_service = get_memory_service()
        
        memories = memory_service.get_user_memories(
            user_id=user_id,
            memory_type=memory_type.value if memory_type else None,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "memories": memories,
            "count": len(memories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{session_id}")
async def get_conversation(
    session_id: str,
    limit: int = Query(default=20, ge=1, le=100)
) -> dict:
    """Get conversation history for a session"""
    try:
        memory_service = get_memory_service()
        
        messages = memory_service.get_conversation_history(
            session_id=session_id,
            limit=limit
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{session_id}")
async def delete_conversation(session_id: str) -> dict:
    """Delete conversation history for a session"""
    try:
        memory_service = get_memory_service()
        memory_service.clear_session(session_id)
        
        return {
            "success": True,
            "message": f"Conversation {session_id} deleted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def memory_health() -> dict:
    """Check memory service health"""
    try:
        memory_service = get_memory_service()
        return {
            "status": "healthy",
            "nocodb_configured": bool(memory_service.api_token)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

