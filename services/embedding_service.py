# services/embedding_service.py - OpenAI and CLIP embedding generation

import os
import base64
import numpy as np
from typing import List, Optional, Union, Tuple
from io import BytesIO

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Constants
TEXT_EMBEDDING_MODEL = "text-embedding-3-small"
TEXT_EMBEDDING_DIMENSIONS = 1536
CLIP_EMBEDDING_DIMENSIONS = 512


class EmbeddingService:
    """Service for generating text and image embeddings"""
    
    def __init__(self):
        self.openai_client = None
        self.clip_model = None
        self.clip_processor = None
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            print("Warning: OPENAI_API_KEY not found, text embeddings will not work")
    
    def _initialize_clip(self):
        """Lazy initialization of CLIP model"""
        if self.clip_model is None:
            try:
                from transformers import CLIPProcessor, CLIPModel
                import torch
                
                model_name = "openai/clip-vit-base-patch32"
                self.clip_model = CLIPModel.from_pretrained(model_name)
                self.clip_processor = CLIPProcessor.from_pretrained(model_name)
                
                # Use GPU if available
                if torch.cuda.is_available():
                    self.clip_model = self.clip_model.cuda()
                    
                print(f"CLIP model loaded: {model_name}")
            except Exception as e:
                print(f"Error loading CLIP model: {e}")
                raise
    
    def get_text_embedding(self, text: str) -> Optional[List[float]]:
        """Generate text embedding using OpenAI"""
        if not self.openai_client:
            print("OpenAI client not initialized")
            return None
        
        try:
            # Clean and truncate text
            text = text.strip()
            if not text:
                return None
            
            # OpenAI has a token limit, truncate if needed
            if len(text) > 8000:
                text = text[:8000]
            
            response = self.openai_client.embeddings.create(
                model=TEXT_EMBEDDING_MODEL,
                input=text,
                dimensions=TEXT_EMBEDDING_DIMENSIONS
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"Error generating text embedding: {e}")
            return None
    
    def get_text_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 100
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches"""
        if not self.openai_client:
            return [None] * len(texts)
        
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Clean texts
            batch = [t.strip()[:8000] if t else "" for t in batch]
            
            try:
                response = self.openai_client.embeddings.create(
                    model=TEXT_EMBEDDING_MODEL,
                    input=batch,
                    dimensions=TEXT_EMBEDDING_DIMENSIONS
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                results.extend(batch_embeddings)
                
            except Exception as e:
                print(f"Error in batch embedding: {e}")
                results.extend([None] * len(batch))
        
        return results
    
    def get_image_embedding(
        self, 
        image_data: Union[str, bytes]
    ) -> Optional[List[float]]:
        """Generate image embedding using CLIP"""
        self._initialize_clip()
        
        if self.clip_model is None:
            return None
        
        try:
            from PIL import Image
            import torch
            
            # Handle base64 or bytes
            if isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            
            # Process image
            inputs = self.clip_processor(images=image, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten().tolist()
            
        except Exception as e:
            print(f"Error generating image embedding: {e}")
            return None


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

