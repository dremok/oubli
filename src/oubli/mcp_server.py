"""MCP Server for Oubli - Fractal memory system for Claude Code.

This module provides MCP tools for memory operations. Claude Code uses these
tools to store and retrieve memories. All intelligent operations (parsing,
synthesis, organizing) happen in Claude Code - these tools are simple CRUD.
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from .storage import MemoryStore
from .core_memory import load_core_memory, save_core_memory, core_memory_exists


# Initialize MCP server
mcp = FastMCP("oubli")

# Global store instance (initialized lazily)
_store: Optional[MemoryStore] = None


def get_store() -> MemoryStore:
    """Get or create the memory store."""
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store


# ============================================================================
# Memory Tools
# ============================================================================

@mcp.tool()
def memory_save(
    summary: str,
    level: int = 0,
    full_text: str = "",
    topics: list[str] = None,
    keywords: list[str] = None,
    source: str = "conversation",
    parent_ids: list[str] = None,
) -> dict:
    """Save a new memory to the store.

    Args:
        summary: Brief summary of the memory (required).
        level: Memory level - 0 for raw, 1+ for synthesized insights.
        full_text: Full text content of the memory.
        topics: List of topic tags.
        keywords: List of keywords for search.
        source: Source of memory - "conversation", "import", or "synthesis".
        parent_ids: IDs of parent memories (for synthesized memories).

    Returns:
        Dict with the new memory's ID.
    """
    store = get_store()
    memory_id = store.add(
        summary=summary,
        level=level,
        full_text=full_text,
        topics=topics or [],
        keywords=keywords or [],
        source=source,
        parent_ids=parent_ids or [],
    )
    return {"id": memory_id, "status": "saved"}


@mcp.tool()
def memory_search(
    query: str,
    limit: int = 5,
    min_level: int = 0,
) -> list[dict]:
    """Search memories by keyword matching.

    Args:
        query: Search query string.
        limit: Maximum number of results to return.
        min_level: Minimum memory level to include.

    Returns:
        List of matching memories with id, summary, level, topics.
    """
    store = get_store()
    results = store.search(query, limit=limit * 2)  # Get extra to filter

    # Filter by min_level
    filtered = [m for m in results if m.level >= min_level][:limit]

    return [
        {
            "id": m.id,
            "summary": m.summary,
            "level": m.level,
            "topics": m.topics,
            "source": m.source,
        }
        for m in filtered
    ]


@mcp.tool()
def memory_get(memory_id: str) -> dict:
    """Get full details of a specific memory by ID.

    Args:
        memory_id: The UUID of the memory to retrieve.

    Returns:
        Full memory details or error if not found.
    """
    store = get_store()
    memory = store.get(memory_id)

    if memory is None:
        return {"error": f"Memory {memory_id} not found"}

    return {
        "id": memory.id,
        "summary": memory.summary,
        "full_text": memory.full_text,
        "level": memory.level,
        "topics": memory.topics,
        "keywords": memory.keywords,
        "source": memory.source,
        "parent_ids": memory.parent_ids,
        "child_ids": memory.child_ids,
        "created_at": memory.created_at,
        "access_count": memory.access_count,
    }


@mcp.tool()
def memory_list(
    level: int = None,
    limit: int = 50,
) -> list[dict]:
    """List memories, optionally filtered by level.

    Args:
        level: If provided, only return memories at this level.
        limit: Maximum number of memories to return.

    Returns:
        List of memories with id, summary, level, topics.
    """
    store = get_store()

    if level is not None:
        memories = store.get_by_level(level, limit=limit)
    else:
        memories = store.get_all(limit=limit)

    return [
        {
            "id": m.id,
            "summary": m.summary,
            "level": m.level,
            "topics": m.topics,
            "source": m.source,
        }
        for m in memories
    ]


@mcp.tool()
def memory_stats() -> dict:
    """Get statistics about the memory store.

    Returns:
        Dict with total count, counts by level, by topic, and by source.
    """
    store = get_store()
    stats = store.get_stats()

    return {
        "total": stats.total,
        "by_level": stats.by_level,
        "by_topic": stats.by_topic,
        "by_source": stats.by_source,
    }


@mcp.tool()
def memory_update(
    memory_id: str,
    summary: str = None,
    full_text: str = None,
    topics: list[str] = None,
    keywords: list[str] = None,
    child_ids: list[str] = None,
) -> dict:
    """Update an existing memory.

    Args:
        memory_id: The UUID of the memory to update.
        summary: New summary (optional).
        full_text: New full text (optional).
        topics: New topics list (optional).
        keywords: New keywords list (optional).
        child_ids: New child IDs list (optional).

    Returns:
        Status dict indicating success or failure.
    """
    store = get_store()

    updates = {}
    if summary is not None:
        updates["summary"] = summary
    if full_text is not None:
        updates["full_text"] = full_text
    if topics is not None:
        updates["topics"] = topics
    if keywords is not None:
        updates["keywords"] = keywords
    if child_ids is not None:
        updates["child_ids"] = child_ids

    if not updates:
        return {"error": "No updates provided"}

    success = store.update(memory_id, **updates)
    if success:
        return {"status": "updated", "id": memory_id}
    else:
        return {"error": f"Memory {memory_id} not found"}


# ============================================================================
# Delete Tools
# ============================================================================

@mcp.tool()
def memory_delete(memory_id: str) -> dict:
    """Delete a specific memory by ID.

    Use this when information becomes outdated or incorrect. For example,
    if the user says "I no longer work at X", search for memories about
    working at X and delete them.

    Args:
        memory_id: The UUID of the memory to delete.

    Returns:
        Status dict indicating success or failure.
    """
    store = get_store()
    success = store.delete(memory_id)

    if success:
        return {"status": "deleted", "id": memory_id}
    else:
        return {"error": f"Memory {memory_id} not found"}


# ============================================================================
# Import Tools
# ============================================================================

@mcp.tool()
def memory_import(
    memories: list[dict],
    source: str = "import",
) -> dict:
    """Import multiple memories at once.

    This tool accepts pre-parsed memories. Claude Code should parse the raw
    text (e.g., Claude.ai export, markdown notes) and extract metadata before
    calling this tool.

    Each memory dict should have:
        - summary (required): Brief summary of the memory
        - full_text (optional): Full text content
        - topics (optional): List of topic tags
        - keywords (optional): List of keywords

    Args:
        memories: List of memory dicts to import.
        source: Source label for all imported memories (default: "import").

    Returns:
        Dict with count of imported memories and their IDs.
    """
    store = get_store()
    imported_ids = []

    for mem in memories:
        summary = mem.get("summary")
        if not summary:
            continue  # Skip memories without summary

        memory_id = store.add(
            summary=summary,
            level=0,
            full_text=mem.get("full_text", ""),
            topics=mem.get("topics", []),
            keywords=mem.get("keywords", []),
            source=source,
            parent_ids=[],
        )
        imported_ids.append(memory_id)

    return {
        "status": "imported",
        "count": len(imported_ids),
        "ids": imported_ids,
    }


# ============================================================================
# Core Memory Tools
# ============================================================================

@mcp.tool()
def core_memory_get() -> dict:
    """Get the current core memory content.

    Core memory is a structured markdown file containing the most important
    information about the user, always loaded at session start.

    Returns:
        Dict with content and exists flag.
    """
    exists = core_memory_exists()
    content = load_core_memory() if exists else ""

    return {
        "exists": exists,
        "content": content,
    }


@mcp.tool()
def core_memory_save(content: str) -> dict:
    """Save new core memory content.

    This replaces the entire core memory file. Claude should generate
    this content by organizing the most important memories into a
    structured markdown format.

    Args:
        content: The markdown content to save as core memory.

    Returns:
        Status dict.
    """
    save_core_memory(content)
    return {"status": "saved", "length": len(content)}


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
