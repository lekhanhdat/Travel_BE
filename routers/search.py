# routers/search.py - Semantic search API endpoints

import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
    EntityType,
    SearchType,
)
from services import get_embedding_service, get_faiss_service

router = APIRouter(prefix="/api/v1/search", tags=["Semantic Search"])


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest) -> SemanticSearchResponse:
    """
    Perform semantic search across travel entities.
    
    Supports text-based semantic search using OpenAI embeddings
    and optional image-based search using CLIP embeddings.
    """
    start_time = time.time()
    
    try:
        embedding_service = get_embedding_service()
        faiss_service = get_faiss_service()
        
        # Get query embedding based on search type
        if request.search_type == SearchType.IMAGE and request.image_base64:
            query_embedding = embedding_service.get_image_embedding(request.image_base64)
            if not query_embedding:
                return SemanticSearchResponse(
                    success=False,
                    query=request.query,
                    results=[],
                    total_count=0,
                    search_time_ms=(time.time() - start_time) * 1000,
                    search_type=request.search_type,
                    error="Failed to generate image embedding"
                )
        else:
            query_embedding = embedding_service.get_text_embedding(request.query)
            if not query_embedding:
                return SemanticSearchResponse(
                    success=False,
                    query=request.query,
                    results=[],
                    total_count=0,
                    search_time_ms=(time.time() - start_time) * 1000,
                    search_type=request.search_type,
                    error="Failed to generate text embedding"
                )
        
        # Convert entity types to strings for FAISS search
        entity_type_strs = None
        if EntityType.ALL not in request.entity_types:
            entity_type_strs = [et.value for et in request.entity_types]
        
        # Search FAISS index
        raw_results = faiss_service.search_text(
            query_embedding,
            top_k=request.top_k,
            min_score=request.min_score,
            entity_types=entity_type_strs
        )
        
        # Convert to response format
        results = []
        for entity_id, entity_type, score, metadata in raw_results:
            results.append(SemanticSearchResult(
                id=entity_id,
                entity_type=EntityType(entity_type),
                title=metadata.get("title", f"Entity {entity_id}"),
                description=metadata.get("description"),
                score=score,
                metadata=metadata,
                image_url=metadata.get("image_url"),
                location=metadata.get("location")
            ))
        
        search_time = (time.time() - start_time) * 1000
        
        return SemanticSearchResponse(
            success=True,
            query=request.query,
            results=results,
            total_count=len(results),
            search_time_ms=search_time,
            search_type=request.search_type
        )
        
    except Exception as e:
        return SemanticSearchResponse(
            success=False,
            query=request.query,
            results=[],
            total_count=0,
            search_time_ms=(time.time() - start_time) * 1000,
            search_type=request.search_type,
            error=str(e)
        )


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(default=5, ge=1, le=10)
) -> dict:
    """
    Get search suggestions based on partial query.
    Uses semantic similarity to find relevant suggestions.
    """
    try:
        embedding_service = get_embedding_service()
        faiss_service = get_faiss_service()
        
        query_embedding = embedding_service.get_text_embedding(query)
        if not query_embedding:
            return {"suggestions": [], "query": query}
        
        results = faiss_service.search_text(
            query_embedding,
            top_k=limit,
            min_score=0.3
        )
        
        suggestions = []
        for entity_id, entity_type, score, metadata in results:
            suggestions.append({
                "text": metadata.get("title", ""),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "score": score
            })
        
        return {"suggestions": suggestions, "query": query}
        
    except Exception as e:
        return {"suggestions": [], "query": query, "error": str(e)}


@router.get("/health")
async def search_health() -> dict:
    """Check semantic search service health"""
    try:
        faiss_service = get_faiss_service()
        return {
            "status": "healthy",
            "text_index_size": faiss_service.text_index.ntotal if faiss_service.text_index else 0,
            "image_index_size": faiss_service.image_index.ntotal if faiss_service.image_index else 0
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

