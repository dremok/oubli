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
    """Save a new Level 0 memory from the current conversation.

    IMPORTANT: Include full_text with enough context for future drill-down.
    This is what gets retrieved when Claude needs complete details later.
    Include relevant conversation turns; summarize tool outputs rather than
    including raw JSON.

    Args:
        summary: Brief 1-2 sentence summary (required). Used in search results.
        level: Memory level - 0 for raw (default), 1+ for synthesized.
        full_text: Complete conversation context for this memory.
        topics: Lowercase topic tags for grouping (e.g., ["work", "python"]).
        keywords: Specific searchable terms.
        source: Source - "conversation" (default), "import", or "synthesis".
        parent_ids: IDs of parent memories (only for synthesized memories).

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
    prefer_higher_level: bool = True,
) -> list[dict]:
    """Search memories by keyword matching. Returns summaries only (no full_text).

    FRACTAL RETRIEVAL: Start with higher-level memories (synthesized insights),
    then drill down to lower levels only if you need more detail. Use parent_ids
    to find the source memories that were synthesized into an insight.

    Args:
        query: Search query string.
        limit: Maximum number of results to return.
        min_level: Minimum memory level to include.
        prefer_higher_level: If True, sort results by level descending (default).

    Returns:
        List of matching memories with id, summary, level, topics, parent_ids.
        Does NOT include full_text - use memory_get to drill down when needed.
    """
    store = get_store()
    results = store.search(query, limit=limit * 3)  # Get extra for filtering/sorting

    # Filter by min_level
    filtered = [m for m in results if m.level >= min_level]

    # Sort by level (higher first) if preferred
    if prefer_higher_level:
        filtered.sort(key=lambda m: m.level, reverse=True)

    return [
        {
            "id": m.id,
            "summary": m.summary,
            "level": m.level,
            "topics": m.topics,
            "source": m.source,
            "parent_ids": m.parent_ids,  # For drill-down to source memories
        }
        for m in filtered[:limit]
    ]


@mcp.tool()
def memory_get(memory_id: str) -> dict:
    """Get full details of a specific memory, INCLUDING full_text.

    DRILL-DOWN: Use this when you need the complete conversation text stored
    in a Level 0 memory. For Level 1+ memories, full_text is empty - use
    parent_ids to drill down to the source memories.

    Args:
        memory_id: The UUID of the memory to retrieve.

    Returns:
        Full memory details including full_text, parent_ids, child_ids.
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
def memory_get_parents(memory_id: str) -> list[dict]:
    """Get summaries of parent memories (for drilling DOWN from a synthesis).

    FRACTAL DRILL-DOWN: When a Level 1+ synthesized memory doesn't have enough
    detail, use this to get the summaries of its source memories. If you still
    need more detail, use memory_get on a specific parent to get its full_text.

    Args:
        memory_id: The UUID of the synthesized memory.

    Returns:
        List of parent memory summaries (no full_text).
    """
    store = get_store()
    memory = store.get(memory_id)

    if memory is None:
        return {"error": f"Memory {memory_id} not found"}

    parents = []
    for pid in memory.parent_ids:
        parent = store.get(pid)
        if parent:
            parents.append({
                "id": parent.id,
                "summary": parent.summary,
                "level": parent.level,
                "topics": parent.topics,
                "parent_ids": parent.parent_ids,  # For further drill-down
            })

    return parents


@mcp.tool()
def memory_list(
    level: int = None,
    limit: int = 50,
) -> list[dict]:
    """List memories, optionally filtered by level. Returns summaries only.

    Use this to browse the memory hierarchy:
    - level=1 to see synthesized insights
    - level=0 to see raw memories
    - No level filter to see everything

    Args:
        level: If provided, only return memories at this level.
        limit: Maximum number of memories to return.

    Returns:
        List of memories with id, summary, level, topics, parent_ids.
        Does NOT include full_text - use memory_get for that.
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
            "parent_ids": m.parent_ids,
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
# Synthesis Tools
# ============================================================================

@mcp.tool()
def memory_synthesize(
    parent_ids: list[str],
    summary: str,
    topics: list[str] = None,
    keywords: list[str] = None,
    delete_parents: bool = False,
) -> dict:
    """Create a synthesized memory from multiple parent memories.

    This creates a Level 1+ memory that abstracts/combines insights from
    lower-level memories. Claude should:
    1. Review related memories (e.g., all music-related ones)
    2. Identify patterns or themes worth abstracting
    3. Create a synthesized insight using this tool
    4. Optionally delete redundant parents (useful for duplicates)

    Example: 5 memories about jazz guitarists → "User has deep appreciation
    for jazz guitar, especially fusion players"

    Args:
        parent_ids: IDs of the memories being synthesized (required).
        summary: The synthesized insight (1-3 sentences).
        topics: Topic tags for the synthesis.
        keywords: Keywords for search.
        delete_parents: If True, delete parent memories after synthesis.
            Use this when parents are duplicates or fully subsumed.

    Returns:
        Dict with the new synthesized memory's ID.
    """
    store = get_store()

    if not parent_ids:
        return {"error": "parent_ids required - must specify which memories to synthesize"}

    # Determine level (max parent level + 1)
    max_parent_level = 0
    for pid in parent_ids:
        parent = store.get(pid)
        if parent:
            max_parent_level = max(max_parent_level, parent.level)

    new_level = max_parent_level + 1

    # Create synthesized memory (skip dedupe since this is intentional)
    memory_id = store.add(
        summary=summary,
        level=new_level,
        full_text="",  # Synthesized memories don't have full_text
        topics=topics or [],
        keywords=keywords or [],
        source="synthesis",
        parent_ids=parent_ids,
        dedupe=False,  # Don't dedupe synthesis results
    )

    if delete_parents:
        # Delete parent memories (they're subsumed by synthesis)
        deleted_count = 0
        for pid in parent_ids:
            if store.delete(pid):
                deleted_count += 1
        return {
            "status": "synthesized",
            "id": memory_id,
            "level": new_level,
            "parent_count": len(parent_ids),
            "parents_deleted": deleted_count,
        }
    else:
        # Update parent memories to link to this child
        for pid in parent_ids:
            parent = store.get(pid)
            if parent:
                new_child_ids = parent.child_ids + [memory_id]
                store.update(pid, child_ids=new_child_ids)

        return {
            "status": "synthesized",
            "id": memory_id,
            "level": new_level,
            "parent_count": len(parent_ids),
        }


@mcp.tool()
def memory_prepare_synthesis(
    level: int = 0,
    similarity_threshold: float = 0.85,
    min_group_size: int = 2,
) -> dict:
    """Prepare a level for synthesis: merge duplicates, return groups for synthesis.

    SYNTHESIS WORKFLOW (call this level by level):
    1. memory_prepare_synthesis(level=0) → merges dupes, returns groups
    2. For each group, create a Level 1 summary via memory_synthesize
    3. memory_prepare_synthesis(level=1) → merges dupes at L1, returns groups
    4. Create Level 2 summaries, etc.

    This tool AUTOMATICALLY MERGES similar memories at the specified level,
    keeping the highest-quality one (most detail/metadata). Then it returns
    groups of related but distinct memories ready for synthesis.

    Args:
        level: Which level to prepare (default: 0).
        similarity_threshold: Jaccard threshold for merging (0.85 = 85% word overlap).
        min_group_size: Minimum group size to return for synthesis (default: 2).

    Returns:
        Dict with merge stats and groups ready for synthesis.
    """
    store = get_store()
    memories = store.get_by_level(level, limit=500)

    # Skip memories that already have children (already synthesized)
    memories = [m for m in memories if not m.child_ids]

    # STEP 1: Find and merge duplicates
    def jaccard(m1, m2):
        w1 = set(m1.summary.lower().split())
        w2 = set(m2.summary.lower().split())
        if not w1 or not w2:
            return 0
        return len(w1 & w2) / len(w1 | w2)

    def quality_score(m):
        ft_len = len(m.full_text) if m.full_text else 0
        return (ft_len, len(m.topics), len(m.keywords))

    # Find duplicate groups
    processed = set()
    merged_count = 0

    for i, m1 in enumerate(memories):
        if m1.id in processed:
            continue

        duplicates = []
        for m2 in memories[i+1:]:
            if m2.id in processed:
                continue
            if jaccard(m1, m2) >= similarity_threshold:
                duplicates.append(m2)
                processed.add(m2.id)

        if duplicates:
            # Keep the best one, delete the rest
            all_in_group = [m1] + duplicates
            sorted_group = sorted(all_in_group, key=quality_score, reverse=True)
            keep = sorted_group[0]
            to_delete = sorted_group[1:]

            for dup in to_delete:
                store.delete(dup.id)
                merged_count += 1

            processed.add(m1.id)

    # STEP 2: Refresh memories after merge and group by topic
    memories = store.get_by_level(level, limit=500)
    memories = [m for m in memories if not m.child_ids]

    by_topic: dict[str, list] = {}
    for m in memories:
        for t in m.topics:
            if t not in by_topic:
                by_topic[t] = []
            by_topic[t].append({
                "id": m.id,
                "summary": m.summary,
                "keywords": m.keywords,
            })

    # Filter by min_group_size
    synthesis_groups = {
        t: mems for t, mems in by_topic.items()
        if len(mems) >= min_group_size
    }

    return {
        "level": level,
        "duplicates_merged": merged_count,
        "memories_remaining": len(memories),
        "synthesis_groups": len(synthesis_groups),
        "groups": synthesis_groups,
        "next_step": f"For each group, create a Level {level + 1} summary using memory_synthesize(parent_ids=[...], summary='...')"
    }


@mcp.tool()
def memory_dedupe(
    dry_run: bool = True,
    threshold: float = 0.85,
) -> dict:
    """Find and optionally remove duplicate memories.

    Uses Jaccard similarity on summary words to detect duplicates.
    For each group of similar memories, keeps the one with the most detail
    (longest full_text or most metadata).

    Args:
        dry_run: If True (default), only report duplicates without deleting.
            Set to False to actually delete duplicates.
        threshold: Similarity threshold (0.0-1.0). Default 0.85 means
            85% word overlap is considered a duplicate.

    Returns:
        Dict with duplicate groups found and action taken.
    """
    store = get_store()
    all_memories = store.get_all(limit=1000)

    # Find duplicate groups
    processed = set()
    duplicate_groups = []

    for i, m1 in enumerate(all_memories):
        if m1.id in processed:
            continue

        words1 = set(m1.summary.lower().split())
        if len(words1) < 3:
            continue

        group = [m1]
        for m2 in all_memories[i+1:]:
            if m2.id in processed:
                continue

            words2 = set(m2.summary.lower().split())
            if len(words2) < 3:
                continue

            # Jaccard similarity
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            similarity = intersection / union if union > 0 else 0

            if similarity >= threshold:
                group.append(m2)
                processed.add(m2.id)

        if len(group) > 1:
            processed.add(m1.id)
            duplicate_groups.append(group)

    # Process each group
    results = []
    deleted_count = 0

    for group in duplicate_groups:
        # Sort by quality: prefer longer full_text, more topics/keywords
        def quality_score(m):
            ft_len = len(m.full_text) if m.full_text else 0
            return (ft_len, len(m.topics), len(m.keywords))

        sorted_group = sorted(group, key=quality_score, reverse=True)
        keep = sorted_group[0]
        duplicates = sorted_group[1:]

        group_info = {
            "keep": {"id": keep.id, "summary": keep.summary[:80]},
            "duplicates": [{"id": d.id, "summary": d.summary[:80]} for d in duplicates],
        }

        if not dry_run:
            for dup in duplicates:
                if store.delete(dup.id):
                    deleted_count += 1
            group_info["deleted"] = len(duplicates)

        results.append(group_info)

    return {
        "dry_run": dry_run,
        "duplicate_groups_found": len(duplicate_groups),
        "total_duplicates": sum(len(g) - 1 for g in duplicate_groups),
        "deleted": deleted_count if not dry_run else 0,
        "groups": results,
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
