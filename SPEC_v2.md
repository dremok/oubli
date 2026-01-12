# Oubli v2: Fractal Memory System for Claude Code

> *"oubli"* (French for "forgetting") — Ironically, a system that never forgets.

## Overview

Oubli is a Claude Code plugin that provides persistent, hierarchical memory with fractal synthesis. It mimics human memory consolidation: raw experiences are stored, then progressively abstracted into higher-level insights over time.

**Goal:** Create a viral, easy-to-install GitHub project that gives Claude Code the persistent memory it deserves.

---

## Core Concept: Fractal Memory

### Memory Levels

```
           ┌─────────────────────────────────────────┐
           │            CORE MEMORY                  │
           │    (~2K tokens, always in context)      │
           │                                         │
           │  The essential "you" - personality,     │
           │  key preferences, life context, work    │
           └─────────────────────┬───────────────────┘
                                 │ (distilled from)
                                 ▼
Level 2+   ○ "Max deeply appreciates jazz guitar, especially fusion"
(insights)  ╱╲
           ╱  ╲
Level 1   ○    ○  "Loves Pat Metheny"  "Studies jazz voicings"
(themes)  │╲  ╱│
          │ ╲╱ │
Level 0   ○ ○ ○ ○  Raw conversation chunks with full text
(raw)
```

- **Core Memory:** A ~2K token distillation of the most important facts about the user. Always loaded. Updated on synthesis AND immediately for fundamental changes.
- **Level 0 (raw):** Complete conversation chunks with full text, summary, metadata
- **Level 1+ (synthesized):** Abstracted insights derived from clustering lower-level memories
- Memories link to their parents (what they were synthesized from) and children (what they synthesized into)

### Core Memory

The Core Memory is a special, always-present context block (~2K tokens) that contains the most essential information about the user. Unlike regular memories that are retrieved on-demand, Core Memory is injected into every conversation via the UserPromptSubmit hook.

**Contents:**
- Identity: Name, location, key relationships
- Work: Role, company, primary skills, current projects
- Family: Parents, siblings, children, partner
- Personality: Communication preferences, values, working style
- Key preferences: Technical choices, tools, patterns
- Current focus: What's top-of-mind right now

**Storage:** `~/.oubli/core_memory.md` - A markdown file that can be viewed/edited directly.

**Update triggers:**
1. **Immediately for fundamental changes:** Family info, work changes, location changes
2. **After synthesis:** When /synthesize completes, Core Memory is regenerated from highest-level insights
3. **Manual:** User can ask Claude to update Core Memory

**Key principle:** Core Memory should be **stable** for most things, but **immediately updated** for fundamental identity/work/family changes.

### Key Principle

Both storage AND retrieval are fractal:
- **Storage:** Raw → synthesized when thresholds are met via auto-triggered /synthesize
- **Retrieval:** Check Core Memory first → search only if needed → drill down to full text only when needed

---

## Architecture

### Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Storage | LanceDB | Embedded (no server), native FTS search, just files |
| Search | BM25 FTS | Native LanceDB full-text search on summary column, incremental indexing |
| Interface | Claude Code Plugin | Hooks + MCP server + slash commands |
| Language | Python | Ecosystem, ease of install |

**Note:** Embeddings (sentence-transformers) are an optional dependency, not required for basic operation.

### Directory Structure

```
oubli/
├── src/oubli/
│   ├── __init__.py
│   ├── cli.py                   # Click CLI: setup, uninstall
│   ├── mcp_server.py            # MCP tools (15 total)
│   ├── storage.py               # LanceDB interface with deduplication + FTS
│   └── core_memory.py           # Core Memory file operations
│   └── data/
│       ├── CLAUDE.md            # Instructions for Claude on using the memory system
│       └── commands/
│           ├── clear-memories.md  # /clear-memories slash command
│           └── synthesize.md      # /synthesize skill
├── pyproject.toml               # Package definition
├── README.md                    # Documentation
├── CLAUDE.md                    # Project development instructions
└── install.sh                   # Legacy manual install script
```

**User data directory (`~/.oubli/`):**
```
~/.oubli/
├── core_memory.md               # Core Memory (~2K tokens, always loaded)
└── memories.lance/              # LanceDB database
```

---

## Data Model

### Memory Schema

```python
@dataclass
class Memory:
    # Content
    summary: str                    # Always present, used for FTS search (~200 tokens max)
    level: int = 0                  # 0 = raw, 1+ = synthesized
    full_text: Optional[str] = None # Only for level 0, stores complete conversation

    # Metadata
    id: str                         # UUID (auto-generated)
    topics: list[str]               # e.g., ["work", "coding", "python"]
    keywords: list[str]             # Extracted keywords for search
    source: str                     # "conversation", "import", "synthesis"

    # Hierarchy
    parent_ids: list[str]           # Memories this was synthesized from
    child_ids: list[str]            # Synthesized memories created from this

    # Timestamps
    created_at: str                 # ISO format datetime
    updated_at: str                 # ISO format datetime
    last_accessed: str              # ISO format datetime

    # Access tracking
    access_count: int = 0

    # Synthesis metadata
    synthesis_attempts: int = 0     # Prevents infinite retry on non-synthesizable clusters
    confidence: float = 1.0         # Confidence score for synthesis

    # Vector embedding (optional, for future semantic search)
    embedding: Optional[list[float]] = None
```

**Storage:** LanceDB with PyArrow schema. Lists are JSON-encoded strings for storage.

### Deduplication

On save, memories are automatically deduplicated using Jaccard similarity (85% word overlap threshold). If a very similar memory already exists, the save is skipped and the existing memory ID is returned.

---

## Installation

### PyPI (Recommended)

```bash
pip install oubli
oubli setup
```

Then restart Claude Code. That's it.

### What Gets Installed

| Component | Location | Description |
|-----------|----------|-------------|
| MCP Server | `claude mcp` registry | 15 memory tools |
| Hooks | `~/.claude/settings.json` | UserPromptSubmit, PreCompact, Stop |
| Slash Commands | `~/.claude/commands/` | `/clear-memories`, `/synthesize` |
| Instructions | `~/.claude/CLAUDE.md` | How Claude should use the memory system |
| Data | `~/.oubli/` | LanceDB database + Core Memory file |

### Uninstall

```bash
oubli uninstall
pip uninstall oubli
```

---

## Plugin Components

### 1. Hooks (in ~/.claude/settings.json)

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python -m oubli.cli inject-context"
      }]
    }],
    "PreCompact": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Context compaction imminent. Silently save any memory-worthy information..."
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Silently save any memory-worthy information from this conversation..."
      }]
    }]
  }
}
```

**UserPromptSubmit:** Command hook that runs CLI to inject Core Memory (~2K tokens) into every prompt via `additionalContext`.

**PreCompact:** Prompt hook that tells Claude to save memories before context compaction.

**Stop:** Prompt hook that tells Claude to save memories and optionally update Core Memory at session end.

### 2. MCP Server Tools (15 total)

#### Retrieval (Fractal Drill-Down)

| Tool | Description |
|------|-------------|
| `memory_search` | Search by BM25 full-text search on summary. Returns summaries only, prefers higher levels. |
| `memory_get` | Get full details INCLUDING full_text (final drill-down) |
| `memory_get_parents` | Get parent memory summaries for drilling down from a synthesis |
| `memory_list` | List memories by level (summaries only) |
| `memory_stats` | Get statistics |

#### Storage

| Tool | Description |
|------|-------------|
| `memory_save` | Save a new memory with deduplication (85% Jaccard threshold) |
| `memory_import` | Bulk import pre-parsed memories |

#### Modification

| Tool | Description |
|------|-------------|
| `memory_update` | Update an existing memory |
| `memory_delete` | Delete a memory (for obsolete info) |

#### Synthesis

| Tool | Description |
|------|-------------|
| `memory_synthesis_needed` | Check if synthesis should run (returns true when unsynthesized L0 count >= threshold) |
| `memory_prepare_synthesis` | Auto-merge duplicates at specified level, return topic groups for synthesis |
| `memory_synthesize` | Create Level 1+ insight from parent memories, optionally delete parents |
| `memory_dedupe` | Manual duplicate cleanup with dry-run option |

#### Core Memory

| Tool | Description |
|------|-------------|
| `core_memory_get` | Get core memory content |
| `core_memory_save` | Save/replace core memory content |

### 3. Slash Commands / Skills

#### /clear-memories
Clears all memories from the database after user confirmation.

#### /synthesize
Full synthesis workflow:
1. Loop through levels (0, 1, 2, ...):
   - `memory_prepare_synthesis(level=N)` - auto-merges duplicates, returns groups
   - For each group, create a summary and call `memory_synthesize`
2. Final step: Regenerate Core Memory from highest-level insights

---

## Synthesis System

### Auto-Triggering

After saving memories, Claude calls `memory_synthesis_needed(threshold=5)`. If it returns `synthesis_needed: true`, Claude silently runs `/synthesize`.

### Synthesis Workflow

```
1. memory_prepare_synthesis(level=0)
   ├─ Finds duplicate L0 memories (Jaccard >= 0.85)
   ├─ MERGES them (keeps best quality, deletes rest)
   └─ Returns topic groups for synthesis

2. For each group:
   └─ memory_synthesize(parent_ids=[...], summary="...")
      Creates Level 1 memory linking to parents

3. memory_prepare_synthesis(level=1)
   ├─ Merges duplicate L1 memories
   └─ Returns groups for L2 synthesis

4. Continue until no more groups...

5. FINAL: Update Core Memory
   ├─ memory_list(level=highest)
   ├─ core_memory_get()
   └─ core_memory_save(regenerated_content)
```

### Fractal Property

The same algorithm applies recursively:
- Level 0 → Level 1 (raw → themes)
- Level 1 → Level 2 (themes → broader insights)
- Level 2 → Level 3 (insights → fundamental understanding)

Each level has duplicate merging before synthesis.

---

## Retrieval Flow

### Core Memory First

Claude checks Core Memory before searching:
- If Core Memory answers the question → respond directly, no search needed
- If more detail needed → then search

### On User Prompt

```
User prompt arrives
        │
        ▼
Core Memory already in context (from UserPromptSubmit hook)
        │
        ▼
┌───────────────────────────────────────┐
│ Is topic covered in Core Memory?      │
│ - Yes → Respond directly              │
│ - No  → Search memories               │
└───────────────────────┬───────────────┘
                        │
                        ▼
            memory_search(query)
                        │
                        ▼
            Need more detail?
                        │
        ┌───────────────┴───────────────┐
        │ Yes                           │ No
        ▼                               │
memory_get_parents(id)                  │
or memory_get(id) for full_text         │
        │                               │
        └───────────────┬───────────────┘
                        │
                        ▼
            Respond with context
```

### Context Budget

| Source | Tokens | When Loaded |
|--------|--------|-------------|
| Core Memory | ~2,000 | Always (UserPromptSubmit hook) |
| Query-relevant memories | ~1,000 | On-demand during conversation |
| Full text retrieval | Variable | On-demand when detail needed |

---

## Proactive Memory Behavior

### Core Principles (from CLAUDE.md)

1. **Core Memory First** - Check Core Memory before searching
2. **Search when needed** - Only if topic not covered in Core Memory
3. **Save automatically** - When user reveals preferences, facts, opinions, decisions
4. **Update Core Memory immediately** for fundamental changes:
   - Family info (any relatives)
   - Work changes (new projects, role changes)
   - Location/identity changes
5. **Auto-trigger synthesis** - Call `memory_synthesis_needed()` after saving, run /synthesize if needed
6. **Be quiet** - No narration, just do it silently

### What to Save

- **Preferences**: "I like X", "I prefer Y"
- **Personal facts**: Work, family, location
- **Opinions**: Strong views on topics
- **Decisions**: Choices made during conversations
- **Interests**: Topics they engage with enthusiastically

### What NOT to Save

- Transient task details
- Generic questions without personal info
- Things already in memory (duplicates auto-detected anyway)

---

## Configuration

All configuration uses sensible defaults. No config file required.

**Storage:** `~/.oubli/memories.lance/`

**Core Memory:** `~/.oubli/core_memory.md` (max ~2K tokens)

**Synthesis threshold:** 5 unsynthesized L0 memories

**Deduplication threshold:** 0.85 Jaccard similarity

---

## Dependencies

```toml
[project]
name = "oubli"
version = "0.1.11"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "lancedb>=0.4.0",
    "pyarrow>=14.0.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
embeddings = [
    "sentence-transformers>=2.2.0",
]
```

---

## Current Implementation Status

### Completed (v0.1.11)

- [x] PyPI installation (`pip install oubli && oubli setup`)
- [x] LanceDB storage with native BM25 full-text search
- [x] Deduplication on save (Jaccard similarity)
- [x] 15 MCP tools including synthesis and fractal drill-down
- [x] Hooks: UserPromptSubmit (core memory), PreCompact, Stop
- [x] /clear-memories slash command
- [x] /synthesize skill with Core Memory update
- [x] Auto-synthesis triggering (`memory_synthesis_needed`)
- [x] `memory_prepare_synthesis` for duplicate merging + grouping
- [x] Immediate Core Memory updates for fundamental changes
- [x] Proactive memory behavior instructions (CLAUDE.md)

### Not Yet Implemented

- [ ] Embeddings for semantic search (optional, using keyword FTS for now)
- [ ] Web UI for browsing memories
- [ ] Memory graph visualization
- [ ] Git-based sync between machines
- [ ] Import from ChatGPT, Gemini

---

## Differences from SPEC.md (v1)

| Feature | SPEC v1 | Current Implementation |
|---------|---------|----------------------|
| Search | Hybrid (BM25 + embeddings) | BM25 FTS only (embeddings optional) |
| Subagents | Synthesizer subagent | Inline synthesis via tools |
| Skills | memory-awareness skill | Proactive behavior in CLAUDE.md |
| Hooks | SessionStart, Stop | UserPromptSubmit, PreCompact, Stop |
| Commands | Multiple /oubli:* commands | /clear-memories, /synthesize |
| Tools | 9 tools | 15 tools |
| Core Memory updates | After synthesis only | Immediate for fundamental changes + after synthesis |
| Deduplication | Not specified | Automatic on save (85% Jaccard) |
| Installation | Manual plugin setup | PyPI + `oubli setup` |

---

## Success Metrics

### For Virality

- One-command install experience (`pip install oubli && oubli setup`)
- Works immediately after restart
- Proactive memory operations (no prompting needed)
- Clear README with feature list

### For Utility

- Retrieval latency < 100ms (BM25 FTS)
- Relevant memories surface consistently
- Synthesis creates genuinely useful abstractions
- Core Memory captures the essential "you"
- No duplicate memories cluttering results

---

## Tagline

**"Give Claude Code the memory it deserves"**
