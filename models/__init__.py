# models/__init__.py - Pydantic models for Semantic Search API

from .search import (
    SemanticSearchRequest,
    SemanticSearchResult,
    SemanticSearchResponse,
    EntityType,
    SearchType,
)

from .chat import (
    RAGChatRequest,
    RAGChatResponse,
    ChatSource,
    SuggestedAction,
)

from .memory import (
    UserMemory,
    MemoryType,
    StoreMemoryRequest,
    ConversationMessage,
    ConversationHistory,
)

__all__ = [
    'SemanticSearchRequest',
    'SemanticSearchResult', 
    'SemanticSearchResponse',
    'EntityType',
    'SearchType',
    'RAGChatRequest',
    'RAGChatResponse',
    'ChatSource',
    'SuggestedAction',
    'UserMemory',
    'MemoryType',
    'StoreMemoryRequest',
    'ConversationMessage',
    'ConversationHistory',
]

