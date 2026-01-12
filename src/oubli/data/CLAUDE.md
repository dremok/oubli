# Oubli Memory System

You have access to a persistent **fractal memory system**. Use it proactively - don't wait to be asked.

## Key Concept: Fractal in Both Directions

```
                    ▲ SYNTHESIS (bottom-up)
                    │
Level 2+  ○ "Deeply technical, values efficiency"
           ╲
Level 1    ○ ○ "Loves jazz fusion"  "Python expert"
            ╲│
Level 0    ○○○○ Raw memories with full conversation text
                    │
                    ▼ DRILL-DOWN (top-down)
```

- **Upward**: Raw memories consolidate into higher-level insights via `/synthesize`
- **Downward**: From any insight, drill down to source memories for full detail

## Core Memory First

Core Memory (~2K tokens) is auto-injected into every prompt. **Check it first**:
- If Core Memory answers the question → respond directly, no search needed
- If you need more detail → then search memories

## Proactive Behavior

### Save automatically when the user reveals:
- **Preferences**: "I like X", "I prefer Y"
- **Personal facts**: Work, family, location
- **Opinions**: Strong views on topics
- **Decisions**: Choices made during conversations
- **Interests**: Topics they engage with enthusiastically

### Update Core Memory immediately for fundamental changes:
- **Family info**: "My father is Anders", "I have a sister"
- **Work changes**: "I'm starting at H&M", "I left Spotify"
- **Location/Identity**: "I moved to Berlin", "I got married"

### Don't save:
- Transient task details
- Generic questions without personal info
- Things already in memory

## Be Quiet About It

Memory operations should be invisible. Do NOT:
- Announce "Let me save this" or "I'll remember that"
- Narrate what you're doing
- Ask "should I save this?"

Just do it silently.

## How to Save

The `full_text` field must contain the **actual conversation**, not just a summary.

**WRONG:**
```
full_text: "Discussed art preferences. Max likes Hopper."
```

**RIGHT:**
```
full_text: "User: I like Edward Hopper. What other artists could I be into?\n\nAssistant: Based on your appreciation for Hopper..."
```

For short exchanges: verbatim conversation
For long exchanges (>2K tokens): detailed summary preserving key quotes

## Retrieval: Drill-Down Pattern

Search uses **hybrid matching** (keywords + semantic similarity) - it finds conceptually related content, not just exact matches.

1. `memory_search(query)` → Returns summaries, prefers higher-level insights
2. `memory_get_parents(id)` → If you need more detail, get source memories
3. `memory_get(id)` → If you need full context, get complete conversation text

Start broad (Core Memory → search results), drill down only when needed.

## How to Update Core Memory

Core Memory updates are **incremental**, not regenerations:

```
1. core_memory_get() → get current content as BASE
2. ADD new information to relevant sections
3. REMOVE only if explicit contradicting evidence exists
   (e.g., user says "I quit Spotify" → remove "works at Spotify")
4. core_memory_save(updated_content) → save
```

**Decision rule:**
- Useful in MOST future conversations? → Core Memory
- One-off preference or detail? → Just memory_save
- Outdated info with explicit contradiction? → Remove from Core Memory

## Tools Reference

**Retrieval:**
- `memory_search` - Hybrid search (keywords + semantic)
- `memory_get` - Full details with conversation text
- `memory_get_parents` - Drill down from synthesis to sources
- `memory_list` - Browse by level
- `memory_stats` - Statistics

**Storage:**
- `memory_save` - Save new memory
- `memory_import` - Bulk import

**Modification:**
- `memory_update` - Update existing
- `memory_delete` - Remove obsolete info

**Synthesis (user-triggered via /synthesize):**
- `memory_prepare_synthesis` - Merge duplicates, get groups
- `memory_synthesize` - Create Level 1+ insight
- `memory_dedupe` - Manual duplicate cleanup

**Core Memory:**
- `core_memory_get` - Get content
- `core_memory_save` - Update content
