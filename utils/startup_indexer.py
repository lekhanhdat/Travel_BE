# utils/startup_indexer.py - Cost-optimized startup indexing for demo environments
"""
Startup Indexer for Semantic Search System

Cost-optimized strategy for demo environments (~250 items):
- Rebuilds indexes on startup if they don't exist
- Takes ~10-30 seconds for 250 items
- Avoids need for persistent storage (saves ~$5/month)
- Uses in-memory indexes after startup
"""

import os
import asyncio
from typing import Optional
from datetime import datetime

# Flag to track if indexing has been done this session
_indexing_completed = False
_indexing_lock = asyncio.Lock()


async def check_and_rebuild_indexes_on_startup():
    """Check if FAISS indexes exist and rebuild if necessary."""
    global _indexing_completed

    async with _indexing_lock:
        if _indexing_completed:
            print("Indexes already built this session")
            return

        from services.faiss_service import get_faiss_service
        faiss_service = get_faiss_service()

        # Check if indexes have data
        if faiss_service.text_index.ntotal > 0:
            print(f"Existing index found with {faiss_service.text_index.ntotal} vectors")
            _indexing_completed = True
            return

        print("No existing index found. Building indexes on startup...")
        start_time = datetime.now()

        try:
            await rebuild_indexes_async()
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"Index rebuild completed in {elapsed:.1f} seconds")
            _indexing_completed = True
        except Exception as e:
            print(f"Error rebuilding indexes: {e}")


async def rebuild_indexes_async():
    """Rebuild all FAISS indexes from NocoDB data"""
    import requests
    from services.embedding_service import get_embedding_service
    from services.faiss_service import get_faiss_service
    from utils.config import get_cached_config

    config = get_cached_config()
    embedding_service = get_embedding_service()
    faiss_service = get_faiss_service()

    headers = {"xc-token": config.nocodb_api_token, "Content-Type": "application/json"}

    tables = [
        ("location", config.nocodb_locations_table_id),
        ("festival", config.nocodb_festivals_table_id),
        ("item", config.nocodb_items_table_id),
    ]

    total_indexed = 0

    for entity_type, table_id in tables:
        if not table_id:
            continue

        try:
            url = f"{config.nocodb_base_url}/api/v2/tables/{table_id}/records"
            response = requests.get(url, headers=headers, params={"limit": 300})
            response.raise_for_status()

            entities = response.json().get("list", [])
            print(f"  Found {len(entities)} {entity_type}s")

            if not entities:
                continue

            texts = []
            valid_entities = []

            for entity in entities:
                text = _build_entity_text(entity, entity_type)
                if text.strip():
                    texts.append(text)
                    valid_entities.append(entity)

            embeddings = embedding_service.get_text_embeddings_batch(texts)

            for entity, embedding in zip(valid_entities, embeddings):
                if embedding is None:
                    continue

                entity_id = entity.get("Id") or entity.get("id")
                title = entity.get("title") or entity.get("name") or entity.get("Title") or ""
                description = entity.get("description") or entity.get("content") or ""

                faiss_service.add_text_embedding(
                    embedding=embedding,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    metadata={"title": title, "description": description[:500]},
                )
                total_indexed += 1

        except Exception as e:
            print(f"  Error indexing {entity_type}s: {e}")

    faiss_service.save_indexes()
    print(f"  Total: {total_indexed} entities indexed")


def _build_entity_text(entity: dict, entity_type: str) -> str:
    """Build text content for embedding generation"""
    parts = []
    title = entity.get("title") or entity.get("name") or entity.get("Title") or ""
    if title:
        parts.append(f"Title: {title}")

    description = entity.get("description") or entity.get("content") or entity.get("Description") or ""
    if description:
        parts.append(f"Description: {description[:1000]}")

    if entity_type == "location":
        address = entity.get("address") or entity.get("Address") or ""
        if address:
            parts.append(f"Address: {address}")

    if entity_type == "festival":
        date = entity.get("date") or entity.get("Date") or ""
        if date:
            parts.append(f"Date: {date}")

    return "\n".join(parts)


def get_index_stats() -> dict:
    """Get current index statistics"""
    from services.faiss_service import get_faiss_service
    faiss_service = get_faiss_service()
    return {
        "text_vectors": faiss_service.text_index.ntotal if faiss_service.text_index else 0,
        "image_vectors": faiss_service.image_index.ntotal if faiss_service.image_index else 0,
        "indexing_completed": _indexing_completed,
    }
