# routers/chat.py - RAG-enhanced chat API endpoints

from fastapi import APIRouter, HTTPException

from models.chat import (
    RAGChatRequest,
    RAGChatResponse,
    ChatSource,
    SuggestedAction,
)
from services import get_rag_service

router = APIRouter(prefix="/api/v1/chat", tags=["RAG Chat"])


@router.post("/rag", response_model=RAGChatResponse)
async def rag_chat(request: RAGChatRequest) -> RAGChatResponse:
    """
    Send a message and receive a RAG-enhanced response.
    
    The response is generated using:
    1. Semantic search to find relevant context
    2. User memory for personalization
    3. Conversation history for continuity
    4. GPT-4o-mini for response generation
    """
    try:
        rag_service = get_rag_service()
        
        result = rag_service.generate_response(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            max_context_items=request.max_context_items,
            include_sources=request.include_sources
        )
        
        # Convert to response model
        sources = [
            ChatSource(
                entity_id=s["entity_id"],
                entity_type=s["entity_type"],
                title=s["title"],
                relevance_score=s["relevance_score"],
                snippet=s.get("snippet")
            )
            for s in result.get("sources", [])
        ]
        
        actions = [
            SuggestedAction(
                action_type=a["action_type"],
                label=a["label"],
                payload=a["payload"]
            )
            for a in result.get("suggested_actions", [])
        ]
        
        return RAGChatResponse(
            success=result["success"],
            message=result["message"],
            sources=sources,
            suggested_actions=actions,
            session_id=result["session_id"],
            tokens_used=result["tokens_used"],
            response_time_ms=result["response_time_ms"],
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-session")
async def clear_chat_session(session_id: str) -> dict:
    """Clear conversation history for a session"""
    try:
        from services import get_memory_service
        memory_service = get_memory_service()
        memory_service.clear_session(session_id)
        return {"success": True, "message": "Session cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/health")
async def chat_health() -> dict:
    """Check RAG chat service health"""
    try:
        rag_service = get_rag_service()
        return {
            "status": "healthy",
            "openai_available": rag_service.openai_client is not None
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

