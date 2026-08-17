from functools import lru_cache
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

def _cosine(a, b):
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
    return float(np.dot(a, b) / denom)

@lru_cache(maxsize=1)
def _get_embedding_model(model_name: str = "BAAI/bge-m3"):
    """Loads the sentence-transformer model once per process"""
    return SentenceTransformer(model_name)

def embed_texts(texts: List[str]) -> np.ndarray:
    """Generates embeddings for a list of texts using a sentence-transformer model."""
    model = _get_embedding_model()
    return model.encode(texts, convert_to_numpy=True)
