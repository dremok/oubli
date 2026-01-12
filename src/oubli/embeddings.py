"""Embedding functions for Oubli using LanceDB's built-in registry.

This module provides access to sentence-transformers embeddings via
LanceDB's embedding function registry. Requires the 'embeddings' extra:
    pip install oubli[embeddings]
"""

from typing import Optional

# Embedding model singleton
_model = None


def get_embedding_model():
    """Get sentence-transformers model from LanceDB registry.

    Uses all-MiniLM-L6-v2 (384 dimensions, ~80MB) - good balance of
    quality and size for semantic search.

    Returns:
        EmbeddingFunction or None if sentence-transformers not installed.
    """
    global _model

    if _model is not None:
        return _model

    try:
        from lancedb.embeddings import get_registry
        _model = get_registry().get("sentence-transformers").create(
            name="all-MiniLM-L6-v2",
            device="cpu"
        )
        return _model
    except ImportError:
        # sentence-transformers not installed
        return None
    except Exception:
        # Model download failed or other error
        return None


def get_embedding_dims() -> int:
    """Get the embedding dimension size."""
    return 384  # all-MiniLM-L6-v2


def generate_embedding(text: str) -> Optional[list[float]]:
    """Generate embedding for a single text.

    Args:
        text: Text to embed.

    Returns:
        List of floats (embedding vector) or None if embeddings unavailable.
    """
    model = get_embedding_model()
    if model is None:
        return None

    try:
        # LanceDB embedding models have compute_source_embeddings method
        embeddings = model.compute_source_embeddings([text])
        return list(embeddings[0])
    except Exception:
        return None


def generate_query_embedding(text: str) -> Optional[list[float]]:
    """Generate embedding for a query text.

    Args:
        text: Query text to embed.

    Returns:
        List of floats (embedding vector) or None if embeddings unavailable.
    """
    model = get_embedding_model()
    if model is None:
        return None

    try:
        # LanceDB embedding models have compute_query_embeddings method
        embeddings = model.compute_query_embeddings([text])
        return list(embeddings[0])
    except Exception:
        return None


def embeddings_available() -> bool:
    """Check if embeddings are available (sentence-transformers installed)."""
    return get_embedding_model() is not None
