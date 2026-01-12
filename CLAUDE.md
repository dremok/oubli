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

- **LanceDB with hybrid search** - Embedded vector database with BM25 FTS + semantic embeddings
- **sentence-transformers by default** - `all-MiniLM-L6-v2` for semantic search (~80MB, downloads on first use)
- **MCP tools are simple CRUD** - Claude Code does the intelligent work (parsing, clustering, summarizing)
- **Slash command for destructive ops** - `/clear-memories` requires explicit user invocation
- **Core Memory is a markdown file** - `~/.oubli/core_memory.md`, human-readable and editable
- **Everything runs locally** - No external services, no API keys needed

## Installation

```bash
pip install oubli
oubli setup
```

Then restart Claude Code.

The setup command installs:
1. **MCP server** - Registered via `claude mcp add` (15 tools)
2. **Hooks** - Written to `~/.claude/settings.json` (UserPromptSubmit, PreCompact, Stop)
3. **Slash commands** - `/clear-memories` and `/synthesize` copied to `~/.claude/commands/`
4. **CLAUDE.md** - Instructions copied to `~/.claude/CLAUDE.md`
5. **Data directory** - `~/.oubli/` created

To uninstall: `oubli uninstall && pip uninstall oubli`

## Package Structure

```
src/oubli/
├── __init__.py
├── cli.py              # CLI with setup/uninstall commands
├── mcp_server.py       # MCP tools for Claude Code (15 tools)
├── storage.py          # LanceDB storage with hybrid search
├── embeddings.py       # Sentence-transformers integration via LanceDB registry
├── core_memory.py      # Core memory file operations
└── data/
    ├── CLAUDE.md       # Instructions installed to ~/.claude/
    └── commands/
        ├── clear-memories.md  # /clear-memories slash command
        └── synthesize.md      # /synthesize skill
```

## Key Files

- `src/oubli/storage.py` - LanceDB-backed MemoryStore with hybrid search (BM25 + vector)
- `src/oubli/embeddings.py` - Sentence-transformers embeddings via LanceDB registry
- `src/oubli/core_memory.py` - Core memory file operations
- `src/oubli/mcp_server.py` - MCP tools for Claude Code integration (15 tools)
- `src/oubli/cli.py` - CLI with setup/uninstall commands and hook support
- `src/oubli/data/CLAUDE.md` - Instructions for Claude on using the memory system
- `SPEC_v2.md` - Full specification document (source of truth for features)

## MCP Tools (15 total)

### Retrieval (Fractal Drill-Down)
- `memory_search` - Hybrid search (BM25 + semantic embeddings), prefers higher levels
- `memory_get_parents` - Get parent memory summaries for drill-down
- `memory_get` - Get full details INCLUDING full_text (final drill-down)
- `memory_list` - List memories by level (summaries only)
- `memory_stats` - Get statistics

### Storage
- `memory_save` - Save with auto-embedding
- `memory_import` - Bulk import pre-parsed memories

### Modification
- `memory_update` - Update an existing memory (re-embeds if summary changed)
- `memory_delete` - Delete a memory (for obsolete info)

### Synthesis
- `memory_synthesis_needed` - Check if synthesis should run (threshold: 5)
- `memory_prepare_synthesis` - Merge duplicates at level, return groups for synthesis
- `memory_synthesize` - Create Level 1+ insight from parent memories
- `memory_dedupe` - Manual duplicate cleanup with dry-run option

### Core Memory
- `core_memory_get` - Get core memory content
- `core_memory_save` - Save/replace core memory content

## Slash Commands

- `/clear-memories` - Clear all memories from the database (user must confirm)
- `/synthesize` - Run full synthesis workflow: merge duplicates, create insights, update Core Memory

## Hooks

- **UserPromptSubmit** - Injects Core Memory into every prompt
- **PreCompact** - Saves memories before context compaction (prevents losing info in long sessions)
- **Stop** - Saves memories at session end

## Current Status (v0.2.3)

### Completed
- PyPI installation (`pip install oubli && oubli setup`)
- **Hybrid search** - BM25 FTS + semantic embeddings (sentence-transformers)
- LanceDB storage with vector column (384 dims, all-MiniLM-L6-v2)
- Auto-embedding on save and update
- Deduplication during synthesis via `memory_prepare_synthesis`
- Memory dataclass with all fields
- CRUD operations (add, get, search, update, delete)
- Core memory file operations
- MCP server with 15 tools (including synthesis and fractal drill-down)
- Session hooks (UserPromptSubmit for core memory, PreCompact + Stop for auto-save)
- `/clear-memories` slash command
- `/synthesize` skill for full synthesis workflow
- `memory_synthesis_needed` to check if synthesis would be useful
- `memory_prepare_synthesis` for merging duplicates before synthesis
- Immediate Core Memory updates for fundamental changes (family, work, identity)
- Instructions for Claude in `src/oubli/data/CLAUDE.md`
- Fractal drill-down retrieval pattern

### Not Yet Implemented
- Web UI for browsing memories
- Memory graph visualization
- Git-based sync between machines

## Development Commands

```bash
# Install in development mode
git clone https://github.com/dremok/oubli.git
cd oubli
pip install -e .
oubli setup

# Visualize memory graph
oubli viz

# Run tests
python -c "from oubli.storage import MemoryStore; store = MemoryStore(); print(store.get_stats())"

# Test CLI
oubli --help
oubli inject-context

# Reset data
rm -rf ~/.oubli/

# Check MCP server loads
python -c "from oubli.mcp_server import mcp; print([t.name for t in mcp._tool_manager._tools.values()])"
```

## Publishing to PyPI

When the user asks to publish a new version:

1. **Bump version** in `pyproject.toml` (use semver: patch for fixes, minor for features, major for breaking)
2. **Build**: `rm -rf dist/ && python -m build`
3. **Ask user for PyPI token** - just say: "I need your PyPI token to publish"
4. **Publish**:
   ```bash
   TWINE_USERNAME=__token__ TWINE_PASSWORD="<token>" python -m twine upload dist/*
   ```
5. **Confirm** with PyPI URL: `https://pypi.org/project/oubli/<version>/`

User can then upgrade in other projects: `pip install --upgrade oubli`

## Data Storage

User data is stored in `~/.oubli/`:
- `memories.lance/` - LanceDB database
- `core_memory.md` - Core Memory file (~2K tokens, always loaded)
