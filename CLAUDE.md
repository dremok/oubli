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

The install script:
1. Creates virtual environment with uv
2. Installs dependencies
3. Registers MCP server with Claude Code
4. Sets up hooks for core memory injection

## Plugin Structure

```
.claude-plugin/
├── plugin.json          # Plugin manifest (MCP server, commands, hooks)
├── CLAUDE.md            # Instructions for Claude on using the memory system
├── commands/
│   └── clear-memories.md  # /clear-memories slash command
└── hooks/
    └── hooks.json       # UserPromptSubmit + Stop hooks
```

## Key Files

- `src/oubli/storage.py` - LanceDB-backed MemoryStore with Memory dataclass
- `src/oubli/core_memory.py` - Core memory file operations
- `src/oubli/mcp_server.py` - MCP tools for Claude Code integration
- `src/oubli/cli.py` - CLI commands for hooks (inject-context, session-start)
- `SPEC.md` - Full specification document (source of truth for features)

## MCP Tools (10 total)

### Memory Operations
- `memory_save` - Save a new memory
- `memory_search` - Search by keyword
- `memory_get` - Get full memory details
- `memory_list` - List all memories
- `memory_stats` - Get statistics
- `memory_update` - Update a memory
- `memory_delete` - Delete a memory (for obsolete info)
- `memory_import` - Bulk import pre-parsed memories

### Core Memory
- `core_memory_get` - Get core memory content
- `core_memory_save` - Save/replace core memory content

## Slash Commands

- `/clear-memories` - Clear all memories from the database (user must confirm)

## Hooks

- **UserPromptSubmit** - Injects Core Memory into every prompt
- **Stop** - Evaluates if memories should be saved at session end

## Current Status

### Completed
- Storage foundation with LanceDB
- Memory dataclass with all fields
- CRUD operations (add, get, search, update, delete)
- Core memory file operations
- MCP server with 10 tools
- Session hooks (UserPromptSubmit for core memory, Stop for auto-save)
- `/clear-memories` slash command
- Plugin structure with bundled MCP, commands, hooks
- Instructions for Claude in plugin CLAUDE.md

### Not Yet Implemented (from SPEC.md)
- `memory_synthesize` tool - Trigger clustering and synthesis
- Embeddings for semantic search (currently keyword-only)
- Synthesizer subagent
- Memory awareness skill

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
