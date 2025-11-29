# services/faiss_service.py - FAISS vector index management

import os
import json
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

import faiss

# Constants
TEXT_EMBEDDING_DIMENSIONS = 1536
CLIP_EMBEDDING_DIMENSIONS = 512
INDEX_DIR = os.environ.get("FAISS_INDEX_DIR", "./faiss_indexes")


class FAISSService:
    """Service for managing FAISS vector indexes"""
    
    def __init__(self):
        self.text_index: Optional[faiss.Index] = None
        self.image_index: Optional[faiss.Index] = None
        self.text_id_map: Dict[int, Dict[str, Any]] = {}  # faiss_id -> metadata
        self.image_id_map: Dict[int, Dict[str, Any]] = {}
        self._ensure_index_dir()
        self._load_indexes()
    
    def _ensure_index_dir(self):
        """Ensure index directory exists"""
        Path(INDEX_DIR).mkdir(parents=True, exist_ok=True)
    
    def _load_indexes(self):
        """Load existing indexes from disk"""
        text_index_path = os.path.join(INDEX_DIR, "text_index.faiss")
        text_map_path = os.path.join(INDEX_DIR, "text_id_map.json")
        image_index_path = os.path.join(INDEX_DIR, "image_index.faiss")
        image_map_path = os.path.join(INDEX_DIR, "image_id_map.json")
        
        # Load text index
        if os.path.exists(text_index_path):
            try:
                self.text_index = faiss.read_index(text_index_path)
                if os.path.exists(text_map_path):
                    with open(text_map_path, 'r') as f:
                        self.text_id_map = {int(k): v for k, v in json.load(f).items()}
                print(f"Loaded text index with {self.text_index.ntotal} vectors")
            except Exception as e:
                print(f"Error loading text index: {e}")
                self._create_text_index()
        else:
            self._create_text_index()
        
        # Load image index
        if os.path.exists(image_index_path):
            try:
                self.image_index = faiss.read_index(image_index_path)
                if os.path.exists(image_map_path):
                    with open(image_map_path, 'r') as f:
                        self.image_id_map = {int(k): v for k, v in json.load(f).items()}
                print(f"Loaded image index with {self.image_index.ntotal} vectors")
            except Exception as e:
                print(f"Error loading image index: {e}")
                self._create_image_index()
        else:
            self._create_image_index()
    
    def _create_text_index(self):
        """Create a new text embedding index"""
        # Using IndexFlatIP for inner product (cosine similarity with normalized vectors)
        self.text_index = faiss.IndexFlatIP(TEXT_EMBEDDING_DIMENSIONS)
        self.text_id_map = {}
        print("Created new text index")
    
    def _create_image_index(self):
        """Create a new image embedding index"""
        self.image_index = faiss.IndexFlatIP(CLIP_EMBEDDING_DIMENSIONS)
        self.image_id_map = {}
        print("Created new image index")
    
    def add_text_embedding(
        self,
        embedding: List[float],
        entity_id: int,
        entity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add a text embedding to the index"""
        vector = np.array([embedding], dtype=np.float32)
        # Normalize for cosine similarity
        faiss.normalize_L2(vector)
        
        faiss_id = self.text_index.ntotal
        self.text_index.add(vector)
        
        self.text_id_map[faiss_id] = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "metadata": metadata or {}
        }
        
        return faiss_id
    
    def add_image_embedding(
        self,
        embedding: List[float],
        entity_id: int,
        entity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add an image embedding to the index"""
        vector = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vector)
        
        faiss_id = self.image_index.ntotal
        self.image_index.add(vector)
        
        self.image_id_map[faiss_id] = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "metadata": metadata or {}
        }
        
        return faiss_id
    
    def search_text(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        min_score: float = 0.0,
        entity_types: Optional[List[str]] = None
    ) -> List[Tuple[int, str, float, Dict[str, Any]]]:
        """Search text index and return (entity_id, entity_type, score, metadata)"""
        if self.text_index.ntotal == 0:
            return []
        
        vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(vector)
        
        # Search more than needed to filter by entity type
        search_k = min(top_k * 3, self.text_index.ntotal)
        scores, indices = self.text_index.search(vector, search_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or score < min_score:
                continue
            
            if idx not in self.text_id_map:
                continue
            
            info = self.text_id_map[idx]
            
            # Filter by entity type
            if entity_types and info["entity_type"] not in entity_types:
                continue
            
            results.append((
                info["entity_id"],
                info["entity_type"],
                float(score),
                info["metadata"]
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def save_indexes(self):
        """Save indexes to disk"""
        faiss.write_index(self.text_index, os.path.join(INDEX_DIR, "text_index.faiss"))
        faiss.write_index(self.image_index, os.path.join(INDEX_DIR, "image_index.faiss"))
        
        with open(os.path.join(INDEX_DIR, "text_id_map.json"), 'w') as f:
            json.dump(self.text_id_map, f)
        with open(os.path.join(INDEX_DIR, "image_id_map.json"), 'w') as f:
            json.dump(self.image_id_map, f)
        
        print("Indexes saved to disk")


# Singleton
_faiss_service: Optional[FAISSService] = None


def get_faiss_service() -> FAISSService:
    """Get or create the FAISS service singleton"""
    global _faiss_service
    if _faiss_service is None:
        _faiss_service = FAISSService()
    return _faiss_service

