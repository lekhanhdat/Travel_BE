# services/memory_service.py - User memory management

import os
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# NocoDB table IDs (to be configured)
USER_MEMORY_TABLE_ID = os.environ.get("NOCODB_USER_MEMORY_TABLE_ID", "")
CONVERSATION_TABLE_ID = os.environ.get("NOCODB_CONVERSATION_TABLE_ID", "")


class MemoryService:
    """Service for managing user memories and conversation history"""
    
    def __init__(self):
        self.base_url = os.environ.get("NOCODB_BASE_URL", "https://app.nocodb.com")
        self.api_token = os.environ.get("NOCODB_API_TOKEN")
        self.headers = {
            "xc-token": self.api_token,
            "Content-Type": "application/json"
        } if self.api_token else {}
        
        # In-memory cache for conversation history (fallback)
        self._conversation_cache: Dict[str, List[Dict]] = {}
        self._memory_cache: Dict[int, List[Dict]] = {}
    
    def _make_request(
        self,
        method: str,
        table_id: str,
        endpoint: str = "",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make a request to NocoDB API"""
        if not self.api_token or not table_id:
            return None
        
        url = f"{self.base_url}/api/v2/tables/{table_id}/records"
        if endpoint:
            url += f"/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                return None
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"NocoDB request error: {e}")
            return None
    
    def store_memory(
        self,
        user_id: int,
        memory_type: str,
        content: str,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> Optional[int]:
        """Store a user memory"""
        data = {
            "userId": user_id,
            "memoryType": memory_type,
            "content": content,
            "confidence": confidence,
            "metadata": metadata or {},
            "createdAt": datetime.utcnow().isoformat()
        }
        
        # Try NocoDB first
        if USER_MEMORY_TABLE_ID:
            result = self._make_request("POST", USER_MEMORY_TABLE_ID, data=data)
            if result:
                return result.get("Id")
        
        # Fallback to cache
        if user_id not in self._memory_cache:
            self._memory_cache[user_id] = []
        
        memory_id = len(self._memory_cache[user_id])
        data["id"] = memory_id
        self._memory_cache[user_id].append(data)
        
        return memory_id
    
    def get_user_memories(
        self,
        user_id: int,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user memories"""
        # Try NocoDB first
        if USER_MEMORY_TABLE_ID:
            where = f"(userId,eq,{user_id})"
            if memory_type:
                where += f"~and(memoryType,eq,{memory_type})"
            
            result = self._make_request(
                "GET",
                USER_MEMORY_TABLE_ID,
                params={"where": where, "limit": limit, "sort": "-createdAt"}
            )
            if result:
                return result.get("list", [])
        
        # Fallback to cache
        memories = self._memory_cache.get(user_id, [])
        if memory_type:
            memories = [m for m in memories if m.get("memoryType") == memory_type]
        return memories[:limit]
    
    def store_conversation_message(
        self,
        session_id: str,
        user_id: Optional[int],
        role: str,
        content: str
    ) -> bool:
        """Store a conversation message"""
        message = {
            "sessionId": session_id,
            "userId": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Try NocoDB
        if CONVERSATION_TABLE_ID:
            result = self._make_request("POST", CONVERSATION_TABLE_ID, data=message)
            if result:
                return True
        
        # Fallback to cache
        if session_id not in self._conversation_cache:
            self._conversation_cache[session_id] = []
        
        self._conversation_cache[session_id].append(message)
        
        # Limit cache size
        if len(self._conversation_cache[session_id]) > 50:
            self._conversation_cache[session_id] = self._conversation_cache[session_id][-50:]
        
        return True
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        # Try NocoDB
        if CONVERSATION_TABLE_ID:
            result = self._make_request(
                "GET",
                CONVERSATION_TABLE_ID,
                params={
                    "where": f"(sessionId,eq,{session_id})",
                    "limit": limit,
                    "sort": "-timestamp"
                }
            )
            if result:
                messages = result.get("list", [])
                return list(reversed(messages))
        
        # Fallback to cache
        messages = self._conversation_cache.get(session_id, [])
        return messages[-limit:]
    
    def clear_session(self, session_id: str) -> bool:
        """Clear conversation history for a session"""
        if session_id in self._conversation_cache:
            del self._conversation_cache[session_id]
        return True


# Singleton
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Get or create the memory service singleton"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service

