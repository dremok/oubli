# Oubli

<img width="35%" alt="image" src="https://github.com/user-attachments/assets/4a3784f7-c139-4af6-8bf8-38c61df1fc7b" />

<br /><br />

**Oubli**: French for "forgetting." (Also a West African fruit so sweet it makes babies forget their mother's milk.)

A memory system that never forgets. Persistent fractal memory for Claude Code.

---

## Quickstart: Bootstrap Your AI's Memory in 5 Minutes

**1. Install Oubli**
```bash
pip install oubli && oubli setup
```
Start Claude Code.

**2. Export what your AI already knows about you**

Go to ChatGPT, Gemini, or Claude.ai and ask:
> "Give me a complete dump of everything you know about me — preferences, facts, work, family, interests and any interesting memories from our conversations."

Copy the output.

**3. Import into Oubli**

Paste into Claude Code and say:
> "Import this into my memory"

Claude parses and stores each fact as a searchable memory.

**4. Synthesize into insights**

Run `/synthesize` to consolidate raw memories into a hierarchy — and generate your Core Memory (the essential "you" that loads in every conversation).

**5. Visualize your memory graph**

```bash
/visualize-memory
```

<img width="827" height="377" alt="Screenshot 2026-01-13 at 09 04 59" src="https://github.com/user-attachments/assets/9d295e7e-6ac9-4a08-a951-eb86e2952750" />

<img width="2240" height="574" alt="Screenshot 2026-01-13 at 09 03 35" src="https://github.com/user-attachments/assets/7cb33dd2-8a48-4944-b611-1a2574d855c5" />


*Your memories, organized. Raw facts at the top, synthesized insights below. Filter by topic, hover for details.*

---

## Features

- **Fractal in Both Directions** - Synthesize raw memories into insights, drill down from insights to source details
- **Hybrid Search** - Combines BM25 keyword search + semantic embeddings for intelligent retrieval
- **Core Memory** - Essential facts about you (~2K tokens), loaded in every conversation
- **Proactive Memory** - Claude searches and saves automatically, no prompting needed
- **Immediate Updates** - Family, work, and identity changes update Core Memory instantly
- **Quiet Operation** - Memory operations happen silently in the background
- **Local-First** - All data stays on your machine, no external services
- **Visual Graph** - Interactive visualization of your memory hierarchy (`oubli viz`)

## Installation

```bash
pip install oubli
oubli setup  # Installs MCP server globally + hooks for current project
```

Then restart Claude Code. The embedding model (~80MB) downloads on first use.

**Important**: Hooks are installed **project-locally** by default (`.claude/settings.local.json`).
This means Oubli only runs in projects where you explicitly enable it.

### Enable in Other Projects

```bash
cd /path/to/your/project
oubli enable
```

### Disable for a Project

```bash
cd /path/to/your/project
oubli disable
```

### Requirements

- Python 3.10+
- [Claude Code](https://claude.ai/code) CLI installed

### Uninstall

```bash
oubli uninstall  # Removes MCP server, global hooks, commands
oubli disable    # (In each project) Remove project-local hooks
pip uninstall oubli
```

## How It Works

### Fractal Memory Hierarchy

The memory system is **fractal in both directions**:

```
           ┌─────────────────────────────────────────┐
           │            CORE MEMORY                  │
           │    (~2K tokens, always in context)      │
           │                                         │
           │  Identity, family, work, preferences    │
           └─────────────────────┬───────────────────┘
                                 │
                    ▲ synthesis  │  drill-down ▼
                                 │
Level 2    ○ "Deeply technical, values efficiency"
            ╲
Level 1    ○ ○ "Loves jazz fusion"  "Python expert"
            ╲│
Level 0    ○○○○ Raw memories with full conversation text
```

- **Upward (Synthesis)**: Raw memories consolidate into higher-level insights
- **Downward (Drill-down)**: From any insight, retrieve its source memories for full detail

| Level | Contains | Use Case |
|-------|----------|----------|
| Core Memory | Essential identity (~2K tokens) | Always loaded, answers most questions |
| Level 1+ | Synthesized insights | Quick context without full details |
| Level 0 | Raw memories + full conversation | When you need exact quotes or specifics |

### Hybrid Search

Oubli uses LanceDB's hybrid search combining:
- **BM25 Full-Text Search** - Finds keyword matches
- **Semantic Embeddings** - Finds conceptually related content (via sentence-transformers)
- **RRF Reranking** - Merges both result sets intelligently

Example: Searching "jazz music" finds memories about "Pat Metheny" and "fusion harmonies" even without exact keyword matches.

### Synthesis (Bottom-Up)

Run `/synthesize` to consolidate raw memories into insights:

1. **Merge duplicates** - Similar memories at each level are combined
2. **Group by topic** - Related memories clustered together
3. **Create insights** - Level 1+ memories synthesize the patterns
4. **Update Core Memory** - Incrementally updated (additions from insights, removals only with contradicting evidence)

### Drill-Down Retrieval (Top-Down)

When you need more detail than a high-level insight provides:

1. **Search** returns synthesized insights first (compact, high-signal)
2. **Get parents** retrieves the source memories that formed an insight
3. **Get full text** retrieves the complete conversation from a Level 0 memory

Nothing is ever lost - every insight links back to its source memories.

## Usage

### Natural Interaction

Just talk naturally. Claude handles memory operations silently:
- "I prefer TypeScript over JavaScript" → Saved automatically
- "What do you know about my work?" → Searches memory
- "I no longer work at Spotify" → Deletes old, saves new, updates Core Memory

### Import Existing Memories

Paste your Claude.ai memory export and ask:
> "Import this into my memory"

Claude parses it into structured memories and optionally creates your Core Memory.

### Slash Commands

- `/synthesize` - Run full synthesis: merge duplicates, create insights, update Core Memory
- `/clear-memories` - Clear all memories (requires confirmation)

### CLI Commands

```bash
oubli viz              # Open interactive memory graph in browser
oubli viz --no-open    # Generate graph.html without opening
```

The visualization shows:
- **Hierarchical tree** - Raw memories at top, synthesized insights below
- **Topic sidebar** - Filter by topic to focus on specific areas
- **Color coding** - Blue (L0 raw), Green (L1), Purple (L2+)
- **Tooltips** - Hover for full summary, topics, keywords

## Data Storage

All data stored locally in `~/.oubli/`:

| File | Description |
|------|-------------|
| `memories.lance/` | LanceDB database with vector embeddings |
| `core_memory.md` | Your Core Memory (human-readable, editable) |
| `graph.html` | Memory visualization (generated by `oubli viz`) |

## What Gets Installed

| Component | Location | Scope | Description |
|-----------|----------|-------|-------------|
| MCP Server | `claude mcp` | Global | 15 memory tools |
| Hooks | `.claude/settings.local.json` | **Per-project** | UserPromptSubmit, PreCompact, Stop |
| Commands | `~/.claude/commands/` | Global | `/clear-memories`, `/synthesize` |
| Instructions | `~/.claude/CLAUDE.md` | Global | How Claude uses the memory system |

**Note**: Hooks are project-local by default. Use `oubli enable` in each project where you want Oubli.

## MCP Tools

### Retrieval
| Tool | Description |
|------|-------------|
| `memory_search` | Hybrid search (BM25 + semantic) |
| `memory_get` | Get full details including conversation text |
| `memory_get_parents` | Drill down from synthesis to source memories |
| `memory_list` | List memories by level |
| `memory_stats` | Get memory statistics |

### Storage
| Tool | Description |
|------|-------------|
| `memory_save` | Save a new memory (auto-embeds) |
| `memory_import` | Bulk import memories |
| `memory_update` | Update an existing memory |
| `memory_delete` | Delete a memory |

### Synthesis
| Tool | Description |
|------|-------------|
| `memory_synthesis_needed` | Check if synthesis should run (threshold: 5) |
| `memory_prepare_synthesis` | Merge duplicates, return groups for synthesis |
| `memory_synthesize` | Create Level 1+ insight from parent memories |
| `memory_dedupe` | Manual duplicate cleanup |

### Core Memory
| Tool | Description |
|------|-------------|
| `core_memory_get` | Get Core Memory content |
| `core_memory_save` | Save Core Memory content |

## Development

```bash
git clone https://github.com/dremok/oubli.git
cd oubli
pip install -e .
oubli setup

# Test storage
python -c "
from oubli.storage import MemoryStore
store = MemoryStore()
print('Embeddings:', store.embeddings_enabled())
store.add(summary='Test memory', topics=['test'])
print(store.search('test'))
"
```

## License

MIT
