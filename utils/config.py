# utils/config.py - Configuration management

import os
from typing import Optional
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration"""
    
    # OpenAI
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    
    # NocoDB
    nocodb_base_url: str = "https://app.nocodb.com"
    nocodb_api_token: str = ""
    nocodb_items_table_id: str = ""
    nocodb_locations_table_id: str = ""
    nocodb_festivals_table_id: str = ""
    nocodb_embeddings_table_id: str = ""
    nocodb_user_memory_table_id: str = ""
    nocodb_conversation_table_id: str = ""
    
    # FAISS
    faiss_index_dir: str = "./faiss_indexes"
    
    # Embedding dimensions
    text_embedding_dim: int = 1536
    image_embedding_dim: int = 512
    
    # Search defaults
    default_top_k: int = 10
    default_min_score: float = 0.5
    
    # Rate limiting
    max_requests_per_minute: int = 60
    
    # Cost tracking
    embedding_cost_per_1k_tokens: float = 0.00002
    chat_cost_per_1k_tokens: float = 0.00015


def get_config() -> Config:
    """Get application configuration from environment variables"""
    return Config(
        # OpenAI
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_embedding_model=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        openai_chat_model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        
        # NocoDB
        nocodb_base_url=os.environ.get("NOCODB_BASE_URL", "https://app.nocodb.com"),
        nocodb_api_token=os.environ.get("NOCODB_API_TOKEN", ""),
        nocodb_items_table_id=os.environ.get("NOCODB_ITEMS_TABLE_ID", "m0s4uwjesun4rl9"),
        nocodb_locations_table_id=os.environ.get("NOCODB_LOCATIONS_TABLE_ID", "mfz84cb0t9a84jt"),
        nocodb_festivals_table_id=os.environ.get("NOCODB_FESTIVALS_TABLE_ID", "mktzgff8mpu2c32"),
        nocodb_embeddings_table_id=os.environ.get("NOCODB_EMBEDDINGS_TABLE_ID", ""),
        nocodb_user_memory_table_id=os.environ.get("NOCODB_USER_MEMORY_TABLE_ID", ""),
        nocodb_conversation_table_id=os.environ.get("NOCODB_CONVERSATION_TABLE_ID", ""),
        
        # FAISS
        faiss_index_dir=os.environ.get("FAISS_INDEX_DIR", "./faiss_indexes"),
        
        # Embedding dimensions
        text_embedding_dim=int(os.environ.get("TEXT_EMBEDDING_DIM", "1536")),
        image_embedding_dim=int(os.environ.get("IMAGE_EMBEDDING_DIM", "512")),
        
        # Search defaults
        default_top_k=int(os.environ.get("DEFAULT_TOP_K", "10")),
        default_min_score=float(os.environ.get("DEFAULT_MIN_SCORE", "0.5")),
        
        # Rate limiting
        max_requests_per_minute=int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "60")),
        
        # Cost tracking
        embedding_cost_per_1k_tokens=float(os.environ.get("EMBEDDING_COST_PER_1K", "0.00002")),
        chat_cost_per_1k_tokens=float(os.environ.get("CHAT_COST_PER_1K", "0.00015")),
    )


# Singleton config instance
_config: Optional[Config] = None


def get_cached_config() -> Config:
    """Get cached configuration instance"""
    global _config
    if _config is None:
        _config = get_config()
    return _config

