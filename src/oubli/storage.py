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

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        d = asdict(self)
        # Convert lists to JSON strings for LanceDB storage
        d['topics'] = json.dumps(d['topics'])
        d['keywords'] = json.dumps(d['keywords'])
        d['parent_ids'] = json.dumps(d['parent_ids'])
        d['child_ids'] = json.dumps(d['child_ids'])
        # Ensure full_text is never None (use empty string)
        if d['full_text'] is None:
            d['full_text'] = ""
        # Remove embedding for now - will add with vector search
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
        # Handle embedding
        if d.get('embedding') is not None and not isinstance(d['embedding'], list):
            d['embedding'] = list(d['embedding'])
        return cls(**d)


@dataclass
class MemoryStats:
    """Statistics about the memory store."""
    total: int
    by_level: dict[int, int]
    by_topic: dict[str, int]
    by_source: dict[str, int]


class MemoryStore:
    """LanceDB-backed storage for memories."""

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

        # Create or open table
        self._init_table()

    def _init_table(self):
        """Initialize the memories table if it doesn't exist."""
        if self.TABLE_NAME in self.db.table_names():
            self.table = self.db.open_table(self.TABLE_NAME)
        else:
            # Create table with explicit schema
            # Need to define types upfront for LanceDB
            schema = pa.schema([
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
                # Skip embedding for now - will add when we implement vector search
            ])
            self.table = self.db.create_table(
                self.TABLE_NAME,
                schema=schema,
            )

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
    ) -> str:
        """Add a new memory.

        Returns:
            The ID of the created memory.
        """
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

        self.table.add([memory.to_dict()])
        return memory.id

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
        """Search memories by keyword matching in summary and full_text.

        For now, uses simple string matching. Vector search added when embeddings available.
        """
        # LanceDB full-text search on summary
        all_memories = self.get_all(limit=1000)

        query_lower = query.lower()
        matches = []
        for m in all_memories:
            score = 0
            # Check summary
            if query_lower in m.summary.lower():
                score += 2
            # Check full_text
            if m.full_text and query_lower in m.full_text.lower():
                score += 1
            # Check keywords
            for kw in m.keywords:
                if query_lower in kw.lower():
                    score += 1
            # Check topics
            for topic in m.topics:
                if query_lower in topic.lower():
                    score += 1

            if score > 0:
                matches.append((score, m))

        # Sort by score descending
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
        for key, value in updates.items():
            if hasattr(memory, key):
                setattr(memory, key, value)

        memory.updated_at = datetime.utcnow().isoformat()

        # Delete old and add new (LanceDB doesn't have in-place update)
        self.table.delete(f"id = '{memory_id}'")
        self.table.add([memory.to_dict()])
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
        # Get current access count
        results = self.table.search().where(f"id = '{memory_id}'").limit(1).to_list()
        if results:
            current = results[0]
            new_count = current.get('access_count', 0) + 1
            now = datetime.utcnow().isoformat()

            # Update (delete + add)
            self.table.delete(f"id = '{memory_id}'")
            current['access_count'] = new_count
            current['last_accessed'] = now
            self.table.add([current])
