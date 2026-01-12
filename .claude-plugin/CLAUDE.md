# Oubli Memory System

You have access to a persistent memory system. Use it to remember important information about the user across sessions.

## Core Memory

Core Memory (~2K tokens) is injected into every prompt automatically. It contains the most important, stable facts about the user: identity, work context, preferences, personality.

**Update Core Memory when:**
- User shares fundamental facts (name, job, family, location)
- Major life/work changes ("I just started at X", "I moved to Y")
- Strong preferences that affect most interactions

**Don't update Core Memory for:**
- Transient interests or one-off topics
- Project-specific details (use regular memories instead)

## Tools

### Saving Memories
- `memory_save` - Save a single memory with summary, topics, keywords
- `memory_import` - Bulk import pre-parsed memories (you parse the text first)

### Retrieving Memories
- `memory_search` - Search by keywords (check before saving duplicates!)
- `memory_get` - Get full details of a specific memory
- `memory_list` - List all memories, optionally by level
- `memory_stats` - Get counts by level, topic, source

### Updating/Deleting
- `memory_update` - Update an existing memory
- `memory_delete` - Delete obsolete memories

### Core Memory
- `core_memory_get` - Get current core memory (usually not needed, it's auto-injected)
- `core_memory_save` - Replace core memory with new content

## Workflows

### When user shares new information
1. `memory_search` to check if this updates existing knowledge
2. If updating: `memory_update` or `memory_delete` the old + `memory_save` new
3. If new: `memory_save` with good topics/keywords
4. If fundamental: also update Core Memory via `core_memory_save`

### When user says something is no longer true
Example: "I no longer work at Spotify"
1. `memory_search` for "Spotify" or "work"
2. `memory_delete` outdated memories
3. `memory_save` the new situation if relevant
4. Update Core Memory if work context changed

### When importing from Claude.ai or notes
1. Parse the text into individual memories (summary, topics, keywords for each)
2. `memory_import` with the parsed list
3. Consider generating/updating Core Memory from the imported data

## Memory Levels
- **Level 0**: Raw memories from conversations
- **Level 1+**: Synthesized insights (future feature)

## Tips
- Keep summaries concise (1-2 sentences)
- Use consistent topic names (lowercase: "work", "music", "coding")
- Add specific keywords for searchability
- Search before saving to avoid duplicates
