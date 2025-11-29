# routers/recommendations.py - Similar items and personalized recommendations endpoints

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services import get_embedding_service, get_faiss_service, get_memory_service

router = APIRouter(prefix="/api/v1", tags=["Recommendations"])


class SimilarItem(BaseModel):
    """Similar item response model"""
    entity_type: str
    entity_id: int
    name: str
    similarity_score: float
    description: Optional[str] = None
    image_url: Optional[str] = None


class SimilarItemsResponse(BaseModel):
    """Response for similar items endpoint"""
    success: bool
    entity_type: str
    entity_id: int
    similar_items: List[SimilarItem]
    error: Optional[str] = None


class Recommendation(BaseModel):
    """Personalized recommendation model"""
    entity_type: str
    entity_id: int
    name: str
    reason: str
    score: float
    description: Optional[str] = None
    images: Optional[List[str]] = None


class RecommendationsResponse(BaseModel):
    """Response for recommendations endpoint"""
    success: bool
    user_id: int
    recommendations: List[Recommendation]
    error: Optional[str] = None


@router.get("/similar/{entity_type}/{entity_id}", response_model=SimilarItemsResponse)
async def get_similar_items(
    entity_type: str,
    entity_id: int,
    limit: int = Query(default=5, ge=1, le=20)
) -> SimilarItemsResponse:
    """
    Get similar items based on vector similarity.
    
    Args:
        entity_type: Type of entity (location, festival, item)
        entity_id: ID of the source entity
        limit: Maximum number of similar items to return
    
    Returns:
        List of similar items with similarity scores
    """
    try:
        faiss_service = get_faiss_service()
        
        # Find the embedding for the source entity
        source_embedding = None
        source_metadata = None
        
        for faiss_id, info in faiss_service.text_id_map.items():
            if info["entity_id"] == entity_id and info["entity_type"] == entity_type:
                # Reconstruct the embedding from FAISS index
                import numpy as np
                source_embedding = faiss_service.text_index.reconstruct(faiss_id)
                source_metadata = info["metadata"]
                break
        
        if source_embedding is None:
            return SimilarItemsResponse(
                success=False,
                entity_type=entity_type,
                entity_id=entity_id,
                similar_items=[],
                error=f"Entity not found: {entity_type}/{entity_id}"
            )
        
        # Search for similar items (get extra to filter out the source)
        results = faiss_service.search_text(
            source_embedding.tolist(),
            top_k=limit + 1,
            min_score=0.3
        )
        
        similar_items = []
        for eid, etype, score, metadata in results:
            # Skip the source entity itself
            if eid == entity_id and etype == entity_type:
                continue
            
            similar_items.append(SimilarItem(
                entity_type=etype,
                entity_id=eid,
                name=metadata.get("title", f"{etype} #{eid}"),
                similarity_score=round(score, 4),
                description=metadata.get("description"),
                image_url=metadata.get("image_url")
            ))
            
            if len(similar_items) >= limit:
                break
        
        return SimilarItemsResponse(
            success=True,
            entity_type=entity_type,
            entity_id=entity_id,
            similar_items=similar_items
        )
        
    except Exception as e:
        return SimilarItemsResponse(
            success=False,
            entity_type=entity_type,
            entity_id=entity_id,
            similar_items=[],
            error=str(e)
        )


@router.get("/recommendations/{user_id}", response_model=RecommendationsResponse)
async def get_recommendations(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=20)
) -> RecommendationsResponse:
    """
    Get personalized recommendations based on user preferences and history.
    """
    try:
        memory_service = get_memory_service()
        embedding_service = get_embedding_service()
        faiss_service = get_faiss_service()
        
        # Get user memories/preferences
        memories = memory_service.get_user_memories(user_id, limit=10)
        
        recommendations = []
        seen_entities = set()
        
        if memories:
            # Build a preference profile from memories
            preference_texts = [m.get("content", "") for m in memories if m.get("content")]
            
            if preference_texts:
                # Create a combined preference query
                combined = " ".join(preference_texts[:5])
                pref_embedding = embedding_service.get_text_embedding(combined)
                
                if pref_embedding:
                    results = faiss_service.search_text(
                        pref_embedding,
                        top_k=limit,
                        min_score=0.4
                    )
                    
                    for eid, etype, score, metadata in results:
                        entity_key = f"{etype}:{eid}"
                        if entity_key in seen_entities:
                            continue
                        seen_entities.add(entity_key)
                        
                        recommendations.append(Recommendation(
                            entity_type=etype,
                            entity_id=eid,
                            name=metadata.get("title", f"{etype} #{eid}"),
                            reason="Based on your preferences",
                            score=round(score, 4),
                            description=metadata.get("description"),
                            images=[metadata.get("image_url")] if metadata.get("image_url") else None
                        ))
        
        # If not enough recommendations, add popular items
        if len(recommendations) < limit:
            needed = limit - len(recommendations)
            # Get top items from the index as fallback
            if faiss_service.text_index.ntotal > 0:
                import numpy as np
                # Use a generic travel query for fallback
                generic_embedding = embedding_service.get_text_embedding(
                    "popular tourist destination Da Nang Vietnam"
                )
                if generic_embedding:
                    results = faiss_service.search_text(
                        generic_embedding,
                        top_k=needed + len(seen_entities),
                        min_score=0.3
                    )
                    
                    for eid, etype, score, metadata in results:
                        entity_key = f"{etype}:{eid}"
                        if entity_key in seen_entities:
                            continue
                        seen_entities.add(entity_key)
                        
                        recommendations.append(Recommendation(
                            entity_type=etype,
                            entity_id=eid,
                            name=metadata.get("title", f"{etype} #{eid}"),
                            reason="Popular destination",
                            score=round(score, 4),
                            description=metadata.get("description"),
                            images=[metadata.get("image_url")] if metadata.get("image_url") else None
                        ))
                        
                        if len(recommendations) >= limit:
                            break
        
        return RecommendationsResponse(
            success=True,
            user_id=user_id,
            recommendations=recommendations
        )
        
    except Exception as e:
        return RecommendationsResponse(
            success=False,
            user_id=user_id,
            recommendations=[],
            error=str(e)
        )

