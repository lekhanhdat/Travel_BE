# routers/__init__.py - API routers for Semantic Search

from .search import router as search_router
from .chat import router as chat_router
from .memory import router as memory_router
from .recommendations import router as recommendations_router

__all__ = [
    'search_router',
    'chat_router',
    'memory_router',
    'recommendations_router',
]

