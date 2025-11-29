# models/search.py - Pydantic models for semantic search

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of entities that can be searched"""
    LOCATION = "location"
    ITEM = "item"
    FESTIVAL = "festival"
    ALL = "all"


class SearchType(str, Enum):
    """Types of search operations"""
    TEXT = "text"
    IMAGE = "image"
    HYBRID = "hybrid"


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., description="Search query text", min_length=1, max_length=500)
    entity_types: List[EntityType] = Field(
        default=[EntityType.ALL],
        description="Types of entities to search"
    )
    search_type: SearchType = Field(
        default=SearchType.TEXT,
        description="Type of search to perform"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of results to return"
    )
    min_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )
    user_id: Optional[int] = Field(
        default=None,
        description="User ID for personalized results"
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64 encoded image for image search"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "beautiful beach with sunset",
                "entity_types": ["location"],
                "search_type": "text",
                "top_k": 10,
                "min_score": 0.5
            }
        }


class SemanticSearchResult(BaseModel):
    """Individual search result"""
    id: int = Field(..., description="Entity ID")
    entity_type: EntityType = Field(..., description="Type of entity")
    title: str = Field(..., description="Entity title/name")
    description: Optional[str] = Field(None, description="Entity description")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    image_url: Optional[str] = Field(None, description="Entity image URL")
    location: Optional[str] = Field(None, description="Location name if applicable")


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search"""
    success: bool = Field(..., description="Whether the search was successful")
    query: str = Field(..., description="Original search query")
    results: List[SemanticSearchResult] = Field(
        default_factory=list,
        description="Search results"
    )
    total_count: int = Field(..., description="Total number of results")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")
    search_type: SearchType = Field(..., description="Type of search performed")
    error: Optional[str] = Field(None, description="Error message if search failed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "beautiful beach",
                "results": [
                    {
                        "id": 1,
                        "entity_type": "location",
                        "title": "My Khe Beach",
                        "description": "Beautiful beach in Da Nang",
                        "score": 0.92,
                        "metadata": {"city": "Da Nang"},
                        "image_url": "https://example.com/beach.jpg"
                    }
                ],
                "total_count": 1,
                "search_time_ms": 45.2,
                "search_type": "text"
            }
        }

