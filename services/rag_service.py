# services/rag_service.py - RAG pipeline orchestration

import os
import time
import uuid
from typing import List, Optional, Dict, Any, Tuple

from openai import OpenAI
from dotenv import load_dotenv

from .embedding_service import get_embedding_service
from .faiss_service import get_faiss_service
from .memory_service import get_memory_service

load_dotenv()

# Constants
RAG_MODEL = os.environ.get("RAG_MODEL", "gpt-4o-mini")
MAX_CONTEXT_TOKENS = 4000


class RAGService:
    """Service for RAG-enhanced chat responses"""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_openai()
        self.embedding_service = get_embedding_service()
        self.faiss_service = get_faiss_service()
        self.memory_service = get_memory_service()
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            print("Warning: OPENAI_API_KEY not found")
    
    def _build_context(
        self,
        query: str,
        user_id: Optional[int] = None,
        max_items: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Build context from semantic search results"""
        sources = []
        context_parts = []
        
        # Get query embedding
        query_embedding = self.embedding_service.get_text_embedding(query)
        if not query_embedding:
            return "", []
        
        # Search for relevant content
        results = self.faiss_service.search_text(
            query_embedding,
            top_k=max_items,
            min_score=0.5
        )
        
        for entity_id, entity_type, score, metadata in results:
            title = metadata.get("title", f"{entity_type} #{entity_id}")
            content = metadata.get("content", "")
            
            context_parts.append(f"[{entity_type.upper()}] {title}:\n{content[:500]}")
            
            sources.append({
                "entity_id": entity_id,
                "entity_type": entity_type,
                "title": title,
                "relevance_score": score,
                "snippet": content[:200] if content else None
            })
        
        # Add user memories if available
        if user_id:
            memories = self.memory_service.get_user_memories(user_id, limit=3)
            if memories:
                memory_context = "\n".join([
                    f"- {m.get('content', '')}" for m in memories
                ])
                context_parts.insert(0, f"[USER PREFERENCES]\n{memory_context}")
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    def _build_system_prompt(self, context: str) -> str:
        """Build system prompt with context"""
        return f"""You are a helpful travel assistant for Da Nang, Vietnam. 
You help users discover locations, cultural items, festivals, and plan their trips.

Use the following context to answer questions. If the context doesn't contain 
relevant information, use your general knowledge but mention that.

CONTEXT:
{context}

GUIDELINES:
- Be friendly and helpful
- Provide specific recommendations when possible
- Include practical information (hours, prices, tips)
- Respond in the same language as the user's question
- If asked about something not in context, say so honestly
"""
    
    def generate_response(
        self,
        message: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        max_context_items: int = 5,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """Generate a RAG-enhanced response"""
        start_time = time.time()
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not self.openai_client:
            return {
                "success": False,
                "message": "AI service not available",
                "sources": [],
                "suggested_actions": [],
                "session_id": session_id,
                "tokens_used": 0,
                "response_time_ms": 0,
                "error": "OpenAI client not initialized"
            }
        
        try:
            # Build context
            context, sources = self._build_context(message, user_id, max_context_items)
            
            # Get conversation history
            history = self.memory_service.get_conversation_history(session_id, limit=5)
            
            # Build messages
            messages = [{"role": "system", "content": self._build_system_prompt(context)}]
            
            # Add history
            for msg in history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Generate response
            completion = self.openai_client.chat.completions.create(
                model=RAG_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens if completion.usage else 0
            
            # Store conversation
            self.memory_service.store_conversation_message(
                session_id, user_id, "user", message
            )
            self.memory_service.store_conversation_message(
                session_id, user_id, "assistant", response_text
            )
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "message": response_text,
                "sources": sources if include_sources else [],
                "suggested_actions": self._generate_actions(sources),
                "session_id": session_id,
                "tokens_used": tokens_used,
                "response_time_ms": response_time,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": "Sorry, I encountered an error processing your request.",
                "sources": [],
                "suggested_actions": [],
                "session_id": session_id,
                "tokens_used": 0,
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    def _generate_actions(self, sources: List[Dict]) -> List[Dict]:
        """Generate suggested actions from sources"""
        actions = []
        for source in sources[:3]:
            actions.append({
                "action_type": "navigate",
                "label": f"View {source['title']}",
                "payload": {
                    "screen": f"{source['entity_type'].title()}Detail",
                    "id": source["entity_id"]
                }
            })
        return actions


# Singleton
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

