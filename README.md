# Oubli

<img width="35%" alt="image" src="https://github.com/user-attachments/assets/4a3784f7-c139-4af6-8bf8-38c61df1fc7b" />

**Oubli**: French for "forgetting." (Also a West African fruit so sweet it makes babies forget their mother's milk.)

A memory system that never forgets. Persistent fractal memory for Claude Code.

## Features

- **Core Memory** - Essential facts about you (~2K tokens), loaded in every conversation
- **Persistent Storage** - Memories survive across sessions, stored locally in LanceDB
- **Smart Import** - Import your Claude.ai memory export with one command
- **Auto-Save** - Optionally save important information at session end
- **Local-First** - No external services, no API keys, your data stays on your machine

## Installation

```bash
git clone https://github.com/dremok/oubli.git
cd oubli
./install.sh
```

Requirements:
- [Claude Code](https://claude.ai/code) CLI installed
- [uv](https://astral.sh/uv) for Python environment management

## Usage

After installation, restart Claude Code. Your Core Memory will be automatically loaded in every conversation.

### Import Existing Memories

Paste your Claude.ai memory export and ask:
> "Import this into my memory"

Claude will parse it into structured memories and optionally create your Core Memory.

### Natural Interaction

Just talk naturally:
- "Remember that I prefer TypeScript over JavaScript"
- "What do you know about my work?"
- "I no longer work at Spotify, update your memory"

### Slash Commands

- `/clear-memories` - Clear all memories (requires confirmation)

## How It Works

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
Level 1+   ○ "Deeply appreciates jazz guitar, especially fusion"
(insights)  ╱╲
           ╱  ╲
Level 0   ○ ○ ○ ○  Raw memories from conversations
(raw)
```

- **Core Memory**: Always loaded, contains the most important stable facts
- **Level 0**: Raw memories from conversations with full context
- **Level 1+**: Synthesized insights (future feature)

## Data Storage

All data is stored locally in `~/.oubli/`:
- `memories.lance/` - LanceDB database
- `core_memory.md` - Your Core Memory (human-readable, editable)

## MCP Tools

Oubli provides 10 MCP tools for memory operations:

| Tool | Description |
|------|-------------|
| `memory_save` | Save a new memory |
| `memory_search` | Search memories by keyword |
| `memory_get` | Get full details of a memory |
| `memory_list` | List all memories |
| `memory_stats` | Get memory statistics |
| `memory_update` | Update an existing memory |
| `memory_delete` | Delete a memory |
| `memory_import` | Bulk import memories |
| `core_memory_get` | Get Core Memory content |
| `core_memory_save` | Save Core Memory content |

## Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
python -c "from oubli.storage import MemoryStore; store = MemoryStore(); print(store.get_stats())"

# Check MCP tools
python -c "from oubli.mcp_server import mcp; print([t.name for t in mcp._tool_manager._tools.values()])"
```

## License

MIT
