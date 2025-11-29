#!/usr/bin/env python3
"""
Data Indexing Script for Semantic Search System

This script fetches all entities from NocoDB and generates embeddings for them.
It builds the FAISS indexes and stores embedding metadata in NocoDB.

Usage:
    python index_data.py [--entity-type location|festival|item|all]

Environment Variables Required:
    NOCODB_BASE_URL - NocoDB API base URL
    NOCODB_API_TOKEN - NocoDB API token
    OPENAI_API_KEY - OpenAI API key for embeddings
"""

import os
import sys
import argparse
import hashlib
import json
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embedding_service import get_embedding_service
from services.faiss_service import get_faiss_service

load_dotenv()

# NocoDB Configuration
NOCODB_BASE_URL = os.environ.get("NOCODB_BASE_URL", "https://app.nocodb.com")
NOCODB_API_TOKEN = os.environ.get("NOCODB_API_TOKEN")

# Table IDs
LOCATIONS_TABLE_ID = os.environ.get("NOCODB_LOCATIONS_TABLE_ID", "mfz84cb0t9a84jt")
ITEMS_TABLE_ID = os.environ.get("NOCODB_ITEMS_TABLE_ID", "m0s4uwjesun4rl9")
FESTIVALS_TABLE_ID = os.environ.get("NOCODB_FESTIVALS_TABLE_ID", "mktzgff8mpu2c32")

HEADERS = {
    "xc-token": NOCODB_API_TOKEN,
    "Content-Type": "application/json"
}


def fetch_all_records(table_id: str) -> List[Dict[str, Any]]:
    """Fetch all records from a NocoDB table"""
    url = f"{NOCODB_BASE_URL}/api/v2/tables/{table_id}/records"
    all_records = []
    offset = 0
    limit = 100
    
    while True:
        params = {"offset": offset, "limit": limit}
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("list", [])
        all_records.extend(records)
        
        if len(records) < limit:
            break
        offset += limit
    
    return all_records


def get_content_hash(content: str) -> str:
    """Generate MD5 hash of content for change detection"""
    return hashlib.md5(content.encode()).hexdigest()


def build_text_for_embedding(entity: Dict, entity_type: str) -> str:
    """Build text content for embedding generation"""
    parts = []
    
    # Title/Name
    title = entity.get("title") or entity.get("name") or entity.get("Title") or ""
    if title:
        parts.append(f"Title: {title}")
    
    # Description/Content
    description = entity.get("description") or entity.get("content") or entity.get("Description") or ""
    if description:
        parts.append(f"Description: {description[:1000]}")  # Limit length
    
    # Location-specific fields
    if entity_type == "location":
        address = entity.get("address") or entity.get("Address") or ""
        if address:
            parts.append(f"Address: {address}")
    
    # Festival-specific fields
    if entity_type == "festival":
        date = entity.get("date") or entity.get("Date") or ""
        if date:
            parts.append(f"Date: {date}")
    
    return "\n".join(parts)


def index_entities(entity_type: str, table_id: str):
    """Index all entities of a given type"""
    print(f"\n📦 Indexing {entity_type}s...")
    
    embedding_service = get_embedding_service()
    faiss_service = get_faiss_service()
    
    # Fetch entities
    entities = fetch_all_records(table_id)
    print(f"   Found {len(entities)} {entity_type}s")
    
    if not entities:
        return
    
    # Build texts for embedding
    texts = []
    valid_entities = []
    
    for entity in entities:
        text = build_text_for_embedding(entity, entity_type)
        if text.strip():
            texts.append(text)
            valid_entities.append(entity)
    
    print(f"   Generating embeddings for {len(texts)} entities...")
    
    # Generate embeddings in batch
    embeddings = embedding_service.get_text_embeddings_batch(texts)
    
    # Add to FAISS index
    indexed = 0
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
            metadata={
                "title": title,
                "description": description[:500],
                "content": description,
            }
        )
        indexed += 1
    
    print(f"   ✅ Indexed {indexed} {entity_type}s")


def main():
    parser = argparse.ArgumentParser(description="Index travel data for semantic search")
    parser.add_argument(
        "--entity-type",
        choices=["location", "festival", "item", "all"],
        default="all",
        help="Type of entities to index"
    )
    args = parser.parse_args()
    
    if not NOCODB_API_TOKEN:
        print("❌ Error: NOCODB_API_TOKEN not set")
        return
    
    print("🚀 Starting data indexing for Semantic Search...")
    
    entity_configs = {
        "location": LOCATIONS_TABLE_ID,
        "festival": FESTIVALS_TABLE_ID,
        "item": ITEMS_TABLE_ID,
    }
    
    if args.entity_type == "all":
        for entity_type, table_id in entity_configs.items():
            index_entities(entity_type, table_id)
    else:
        index_entities(args.entity_type, entity_configs[args.entity_type])
    
    # Save indexes
    faiss_service = get_faiss_service()
    faiss_service.save_indexes()
    
    print(f"\n✅ Indexing complete!")
    print(f"   Text index size: {faiss_service.text_index.ntotal} vectors")


if __name__ == "__main__":
    main()

