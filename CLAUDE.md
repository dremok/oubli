# CLAUDE.md

## Project: Oubli - Fractal Memory System for Claude Code

A Claude Code plugin that provides persistent, hierarchical memory with fractal synthesis.

## Working Style Preferences

- **Rapid prototyping** - Get working features fast, avoid over-engineering upfront
- **Phase-based development** - Complete one phase, hand back control for testing/commits, then proceed
- **LLM-driven from the start** - All intelligent operations (parsing, synthesis, core memory generation) run inside Claude Code
- **Test early, test often** - Each phase should have manual test steps before moving on
- **Use uv for virtual environments** - Virtual env at `.venv/`

## Architecture Decisions

- **LanceDB from the start** - Embedded vector database, avoids JSON→LanceDB migration pain later
- **MCP tools are simple CRUD** - Claude Code does the intelligent work (parsing, clustering, summarizing)
- **Slash command for destructive ops** - `/clear-memories` requires explicit user invocation
- **Core Memory is a markdown file** - `~/.oubli/core_memory.md`, human-readable and editable
- **Everything runs locally** - No external services, no API keys needed

## Installation

```bash
# Clone and install
git clone https://github.com/dremok/oubli.git
cd oubli
./install.sh
```

The install script installs:
1. **Virtual environment** - `.venv/` with dependencies
2. **MCP server** - Registered via `claude mcp add`
3. **Hooks** - Written to `~/.claude/settings.json`
4. **Slash command** - `/clear-memories` copied to `~/.claude/commands/`
5. **CLAUDE.md** - Instructions copied to `~/.claude/CLAUDE.md`
6. **Data directory** - `~/.oubli/` created

## Plugin Structure

```
.claude-plugin/
├── plugin.json          # Plugin manifest (MCP server, commands, hooks)
├── CLAUDE.md            # Instructions for Claude on using the memory system
├── commands/
│   └── clear-memories.md  # /clear-memories slash command
└── hooks/
    └── hooks.json       # UserPromptSubmit, PreCompact, Stop hooks
```

## Key Files

- `src/oubli/storage.py` - LanceDB-backed MemoryStore with Memory dataclass
- `src/oubli/core_memory.py` - Core memory file operations
- `src/oubli/mcp_server.py` - MCP tools for Claude Code integration
- `src/oubli/cli.py` - CLI commands for hooks (inject-context, session-start)
- `SPEC.md` - Full specification document (source of truth for features)

## MCP Tools (13 total)

### Retrieval (Fractal Drill-Down)
- `memory_search` - Search summaries, prefers higher levels, returns parent_ids
- `memory_get_parents` - Get parent memory summaries for drill-down
- `memory_get` - Get full details INCLUDING full_text (final drill-down)
- `memory_list` - List memories by level (summaries only)
- `memory_stats` - Get statistics

### Storage
- `memory_save` - Save a new memory with summary + full_text
- `memory_import` - Bulk import pre-parsed memories

### Modification
- `memory_update` - Update an existing memory
- `memory_delete` - Delete a memory (for obsolete info)

### Synthesis
- `memory_get_synthesis_candidates` - Find topics ready for synthesis
- `memory_synthesize` - Create Level 1+ insight from parent memories

### Core Memory
- `core_memory_get` - Get core memory content
- `core_memory_save` - Save/replace core memory content

## Slash Commands

- `/clear-memories` - Clear all memories from the database (user must confirm)

## Hooks

- **UserPromptSubmit** - Injects Core Memory into every prompt
- **PreCompact** - Saves memories before context compaction (prevents losing info in long sessions)
- **Stop** - Saves memories at session end

## Current Status

### Completed
- Storage foundation with LanceDB
- Memory dataclass with all fields
- CRUD operations (add, get, search, update, delete)
- Core memory file operations
- MCP server with 13 tools (including synthesis and fractal drill-down)
- Session hooks (UserPromptSubmit for core memory, PreCompact + Stop for auto-save)
- `/clear-memories` slash command
- Plugin structure with bundled MCP, commands, hooks
- Proactive memory behavior (search before responding, save automatically)
- Instructions for Claude in plugin CLAUDE.md
- Fractal drill-down retrieval pattern

### Not Yet Implemented (from SPEC.md)
- Embeddings for semantic search (currently keyword-only)
- Easy one-command plugin installation (currently requires git clone + install.sh)

## Development Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
python -c "from oubli.storage import MemoryStore; store = MemoryStore(); print(store.get_stats())"

# Test CLI
python -m oubli.cli inject-context

# Reset data
rm -rf ~/.oubli/

# Check MCP server loads
python -c "from oubli.mcp_server import mcp; print([t.name for t in mcp._tool_manager._tools.values()])"

# Test plugin locally
claude --plugin-dir /Users/maxleander/code/oubli/.claude-plugin
```

## Data Storage

User data is stored in `~/.oubli/`:
- `memories.lance/` - LanceDB database
- `core_memory.md` - Core Memory file (~2K tokens, always loaded)
