"""Storage layer for Oubli using LanceDB."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid
import json

import lancedb
import pyarrow as pa


# Default data directory
DEFAULT_DATA_DIR = Path.home() / ".oubli"

# Embedding dimensions for all-MiniLM-L6-v2
EMBEDDING_DIMS = 384


@dataclass
class Memory:
    """A memory entry in the fractal memory system.

    Level 0: Raw memories from conversations/imports
    Level 1+: Synthesized insights from clustering lower-level memories
    """
    # Content
    summary: str
    level: int = 0
    full_text: Optional[str] = None

    # Metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    source: str = "conversation"  # "conversation", "import", "synthesis"

    # Hierarchy (for synthesis tracking)
    parent_ids: list[str] = field(default_factory=list)  # Memories this was synthesized from
    child_ids: list[str] = field(default_factory=list)   # Memories that reference this

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Access tracking
    access_count: int = 0

    # Synthesis metadata
    synthesis_attempts: int = 0
    confidence: float = 1.0

    # Vector embedding (optional, for semantic search)
    embedding: Optional[list[float]] = None

    def to_dict(self, include_vector: bool = False) -> dict:
        """Convert to dictionary for storage.

        Args:
            include_vector: If True, include vector column for hybrid search.
        """
        d = asdict(self)
        # Convert lists to JSON strings for LanceDB storage
        d['topics'] = json.dumps(d['topics'])
        d['keywords'] = json.dumps(d['keywords'])
        d['parent_ids'] = json.dumps(d['parent_ids'])
        d['child_ids'] = json.dumps(d['child_ids'])
        # Ensure full_text is never None (use empty string)
        if d['full_text'] is None:
            d['full_text'] = ""
        # Handle embedding/vector column
        if include_vector and d.get('embedding') is not None:
            d['vector'] = d['embedding']
        del d['embedding']
        return d

    @classmethod
    def from_dict(cls, d: dict) -> 'Memory':
        """Create Memory from dictionary."""
        # Parse JSON strings back to lists
        d = d.copy()
        if isinstance(d.get('topics'), str):
            d['topics'] = json.loads(d['topics'])
        if isinstance(d.get('keywords'), str):
            d['keywords'] = json.loads(d['keywords'])
        if isinstance(d.get('parent_ids'), str):
            d['parent_ids'] = json.loads(d['parent_ids'])
        if isinstance(d.get('child_ids'), str):
            d['child_ids'] = json.loads(d['child_ids'])
        # Handle embedding/vector column
        if 'vector' in d:
            d['embedding'] = list(d['vector']) if d['vector'] is not None else None
            del d['vector']
        elif d.get('embedding') is not None and not isinstance(d['embedding'], list):
            d['embedding'] = list(d['embedding'])
        # Remove any extra fields from LanceDB (like _distance, _relevance_score)
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        d = {k: v for k, v in d.items() if k in known_fields}
        return cls(**d)


@dataclass
class MemoryStats:
    """Statistics about the memory store."""
    total: int
    by_level: dict[int, int]
    by_topic: dict[str, int]
    by_source: dict[str, int]


class MemoryStore:
    """LanceDB-backed storage for memories with optional hybrid search."""

    TABLE_NAME = "memories"

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the memory store.

        Args:
            data_dir: Directory for storing data. Defaults to ~/.oubli/
        """
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize LanceDB
        db_path = self.data_dir / "memories.lance"
        self.db = lancedb.connect(str(db_path))

        # Try to load embedding model (optional)
        self._embedding_model = None
        self._embeddings_available = False
        try:
            from .embeddings import get_embedding_model, embeddings_available
            if embeddings_available():
                self._embedding_model = get_embedding_model()
                self._embeddings_available = True
        except ImportError:
            pass  # sentence-transformers not installed

        # Create or open table
        self._init_table()

    def _init_table(self):
        """Initialize the memories table if it doesn't exist."""
        if self.TABLE_NAME in self.db.table_names():
            self.table = self.db.open_table(self.TABLE_NAME)
            # Check if we need to add vector column to existing table
            self._ensure_vector_column()
        else:
            # Create table with explicit schema
            schema_fields = [
                pa.field("id", pa.string()),
                pa.field("summary", pa.string()),
                pa.field("level", pa.int64()),
                pa.field("full_text", pa.string()),
                pa.field("topics", pa.string()),  # JSON-encoded list
                pa.field("keywords", pa.string()),  # JSON-encoded list
                pa.field("source", pa.string()),
                pa.field("parent_ids", pa.string()),  # JSON-encoded list
                pa.field("child_ids", pa.string()),  # JSON-encoded list
                pa.field("created_at", pa.string()),
                pa.field("updated_at", pa.string()),
                pa.field("last_accessed", pa.string()),
                pa.field("access_count", pa.int64()),
                pa.field("synthesis_attempts", pa.int64()),
                pa.field("confidence", pa.float64()),
            ]
            # Add vector column if embeddings are available
            if self._embeddings_available:
                schema_fields.append(
                    pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIMS))
                )

            schema = pa.schema(schema_fields)
            self.table = self.db.create_table(
                self.TABLE_NAME,
                schema=schema,
            )
            # Create FTS index on summary for keyword search
            self._ensure_fts_index()

    def _ensure_vector_column(self):
        """Add vector column to existing table if embeddings are now available."""
        if not self._embeddings_available:
            return

        # Check if vector column already exists
        try:
            schema = self.table.schema
            field_names = [f.name for f in schema]
            if 'vector' not in field_names:
                # LanceDB supports adding columns via merge
                # For now, we'll add vectors incrementally on new adds
                # Existing records will have NULL vectors and use FTS-only search
                pass
        except Exception:
            pass

    def _ensure_fts_index(self):
        """Create native FTS index on summary (supports incremental updates)."""
        try:
            indices = self.table.list_indices()
            fts_exists = any(
                getattr(idx, 'index_type', None) == 'FTS'
                for idx in indices
            )
            if not fts_exists:
                # Use native FTS (not tantivy) for incremental indexing support
                self.table.create_fts_index('summary', use_tantivy=False, replace=True)
        except Exception:
            try:
                self.table.create_fts_index('summary', use_tantivy=False, replace=True)
            except Exception:
                pass  # Index may already exist or table is empty

    def add(
        self,
        summary: str,
        full_text: Optional[str] = None,
        level: int = 0,
        topics: Optional[list[str]] = None,
        keywords: Optional[list[str]] = None,
        source: str = "conversation",
        parent_ids: Optional[list[str]] = None,
        embedding: Optional[list[float]] = None,
        dedupe: bool = True,
    ) -> str:
        """Add a new memory.

        Args:
            dedupe: If True, skip adding if a very similar memory exists.

        Returns:
            The ID of the created memory, or existing memory ID if duplicate.
        """
        # Check for duplicates by searching for similar summaries
        if dedupe:
            existing = self._find_duplicate(summary)
            if existing:
                return existing.id

        # Generate embedding if model available and not provided
        if embedding is None and self._embeddings_available:
            try:
                from .embeddings import generate_embedding
                embedding = generate_embedding(summary)
            except Exception:
                pass  # Fall back to no embedding

        memory = Memory(
            summary=summary,
            full_text=full_text,
            level=level,
            topics=topics or [],
            keywords=keywords or [],
            source=source,
            parent_ids=parent_ids or [],
            embedding=embedding,
        )

        self.table.add([memory.to_dict(include_vector=self._has_vector_column())])
        return memory.id

    def _has_vector_column(self) -> bool:
        """Check if table has vector column."""
        try:
            schema = self.table.schema
            return any(f.name == 'vector' for f in schema)
        except Exception:
            return False

    def _find_duplicate(self, summary: str, threshold: float = 0.85) -> Optional[Memory]:
        """Find an existing memory with very similar summary.

        Uses simple word overlap ratio for similarity.
        """
        summary_words = set(summary.lower().split())
        if len(summary_words) < 3:
            return None

        # Search for potential matches
        try:
            # Take first few significant words for search
            search_terms = ' '.join(list(summary_words)[:3])
            candidates = self.search(search_terms, limit=5)

            for candidate in candidates:
                candidate_words = set(candidate.summary.lower().split())
                if not candidate_words:
                    continue

                # Jaccard similarity
                intersection = len(summary_words & candidate_words)
                union = len(summary_words | candidate_words)
                similarity = intersection / union if union > 0 else 0

                if similarity >= threshold:
                    return candidate
        except Exception:
            pass

        return None

    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID."""
        results = self.table.search().where(f"id = '{memory_id}'").limit(1).to_list()
        if not results:
            return None

        # Update access tracking
        self._update_access(memory_id)
        return Memory.from_dict(results[0])

    def get_all(self, limit: int = 1000) -> list[Memory]:
        """Get all memories."""
        results = self.table.search().limit(limit).to_list()
        return [Memory.from_dict(r) for r in results]

    def get_by_level(self, level: int, limit: int = 100) -> list[Memory]:
        """Get memories at a specific level."""
        results = self.table.search().where(f"level = {level}").limit(limit).to_list()
        return [Memory.from_dict(r) for r in results]

    def search(self, query: str, limit: int = 10) -> list[Memory]:
        """Search memories using hybrid search (FTS + vector) when available.

        When embeddings are available, uses hybrid search combining:
        - BM25 full-text search on summary (keyword matches)
        - Vector similarity search (semantic matches)
        - RRF (Reciprocal Rank Fusion) to merge results

        Falls back to FTS-only when embeddings not available.
        """
        if not query or not query.strip():
            return []

        try:
            # Ensure FTS index exists
            self._ensure_fts_index()

            # Use hybrid search if embeddings and vector column available
            if self._embeddings_available and self._has_vector_column():
                try:
                    from .embeddings import generate_query_embedding
                    query_embedding = generate_query_embedding(query)

                    if query_embedding is not None:
                        # Hybrid search: FTS + vector with RRF reranking
                        # Must pass both vector and text query separately
                        results = (
                            self.table
                            .search(query_type='hybrid')
                            .vector(query_embedding)
                            .text(query)
                            .limit(limit)
                            .to_list()
                        )
                        return [Memory.from_dict(r) for r in results]
                except Exception:
                    pass  # Fall through to FTS-only

            # FTS-only search (fallback or when no embeddings)
            results = (
                self.table
                .search(query, query_type='fts', fts_columns='summary')
                .limit(limit)
                .to_list()
            )
            return [Memory.from_dict(r) for r in results]
        except Exception:
            # Fallback to basic search if FTS fails (e.g., empty table)
            return self._fallback_search(query, limit)

    def _fallback_search(self, query: str, limit: int = 10) -> list[Memory]:
        """Fallback search using simple string matching."""
        all_memories = self.get_all(limit=1000)
        query_words = [w.lower() for w in query.split() if len(w) >= 2]
        if not query_words:
            return []

        matches = []
        for m in all_memories:
            score = 0
            summary_lower = m.summary.lower()
            full_text_lower = m.full_text.lower() if m.full_text else ""

            for word in query_words:
                if word in summary_lower:
                    score += 2
                if word in full_text_lower:
                    score += 1

            if score > 0:
                matches.append((score, m))

        matches.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in matches[:limit]]

    def update(self, memory_id: str, **updates) -> bool:
        """Update a memory.

        Args:
            memory_id: ID of memory to update
            **updates: Fields to update

        Returns:
            True if updated, False if not found
        """
        memory = self.get(memory_id)
        if not memory:
            return False

        # Apply updates
        summary_changed = False
        for key, value in updates.items():
            if hasattr(memory, key):
                if key == 'summary' and value != memory.summary:
                    summary_changed = True
                setattr(memory, key, value)

        memory.updated_at = datetime.utcnow().isoformat()

        # Regenerate embedding if summary changed
        if summary_changed and self._embeddings_available:
            try:
                from .embeddings import generate_embedding
                memory.embedding = generate_embedding(memory.summary)
            except Exception:
                pass

        # Delete old and add new (LanceDB doesn't have in-place update)
        self.table.delete(f"id = '{memory_id}'")
        self.table.add([memory.to_dict(include_vector=self._has_vector_column())])
        return True

    def delete(self, memory_id: str) -> bool:
        """Delete a memory.

        Returns:
            True if deleted, False if not found
        """
        memory = self.get(memory_id)
        if not memory:
            return False

        self.table.delete(f"id = '{memory_id}'")
        return True

    def delete_all(self) -> int:
        """Delete all memories.

        Returns:
            Number of memories deleted.
        """
        count = len(self.get_all())
        if count > 0:
            # Drop and recreate table
            self.db.drop_table(self.TABLE_NAME)
            self._init_table()
        return count

    def get_stats(self) -> MemoryStats:
        """Get statistics about the memory store."""
        all_memories = self.get_all()

        by_level: dict[int, int] = {}
        by_topic: dict[str, int] = {}
        by_source: dict[str, int] = {}

        for m in all_memories:
            # Count by level
            by_level[m.level] = by_level.get(m.level, 0) + 1

            # Count by topic
            for topic in m.topics:
                by_topic[topic] = by_topic.get(topic, 0) + 1

            # Count by source
            by_source[m.source] = by_source.get(m.source, 0) + 1

        return MemoryStats(
            total=len(all_memories),
            by_level=by_level,
            by_topic=by_topic,
            by_source=by_source,
        )

    def _update_access(self, memory_id: str):
        """Update access tracking for a memory."""
        # Get current record (raw dict to preserve all fields including vector)
        results = self.table.search().where(f"id = '{memory_id}'").limit(1).to_list()
        if results:
            current = dict(results[0])
            new_count = current.get('access_count', 0) + 1
            now = datetime.utcnow().isoformat()

            # Update (delete + add)
            self.table.delete(f"id = '{memory_id}'")
            current['access_count'] = new_count
            current['last_accessed'] = now
            # Remove any search result fields
            current.pop('_distance', None)
            current.pop('_relevance_score', None)
            self.table.add([current])

    def embeddings_enabled(self) -> bool:
        """Check if embeddings are enabled and working."""
        return self._embeddings_available and self._has_vector_column()
