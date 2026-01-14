# CLAUDE.md

## Project: Oubli - Fractal Memory System for Claude Code

A Claude Code plugin that provides persistent, hierarchical memory with fractal synthesis.

## Crucial Memory Rule

**CRUCIAL information must be stored in BOTH Oubli AND this CLAUDE.md file.**

Oubli memories require a search to find. CLAUDE.md is always loaded. For operational info that must never be forgotten (credential locations, publishing workflows, key file paths), put it here so it's always available.

Examples of crucial info:
- Credential/token locations (like PyPI token at `~/.config/pypi/token`)
- Publishing and deployment workflows
- Project-specific operational commands

**Never say "I'll remember that" without actually persisting it.** If something is worth remembering, edit this file immediately.

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
- **Config local, data global** - Config installed per-project, memories shared across all projects

## Installation

```bash
pip install oubli
cd /path/to/project
oubli setup
```

Then restart Claude Code.

### What Gets Installed

**Per-project (local):**
- `.mcp.json` - MCP server registration
- `.claude/settings.local.json` - Hooks
- `.claude/commands/` - Slash commands
- `.claude/CLAUDE.md` - Instructions

**Shared (global):**
- `~/.oubli/` - Data directory (memories + core memory)

To uninstall: `oubli uninstall` then `pip uninstall oubli`

## Package Structure

```
src/oubli/
├── __init__.py
├── cli.py              # CLI with setup/uninstall commands
├── config.py           # Data directory resolution (always ~/.oubli/)
├── mcp_server.py       # MCP tools for Claude Code (15 tools)
├── storage.py          # LanceDB storage with hybrid search
├── embeddings.py       # Sentence-transformers integration via LanceDB registry
├── core_memory.py      # Core memory file operations
├── viz.py              # Memory graph visualization
└── data/
    ├── CLAUDE.md       # Instructions installed to .claude/
    └── commands/
        ├── clear-memories.md    # /clear-memories slash command
        ├── synthesize.md        # /synthesize skill
        └── visualize-memory.md  # /visualize-memory command
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

## Current Status (v0.4.8)

### Completed
- PyPI installation (`pip install oubli && oubli setup`)
- **Local-only installation** - Instructions installed to `.claude/CLAUDE.md` per-project (not global)
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
- **Memory graph visualization** (`oubli viz` / `/visualize-memory`)
- **Diagnostic command** (`oubli doctor`) for troubleshooting

### Not Yet Implemented
- Web UI for browsing memories
- Git-based sync between machines

## Development Commands

```bash
# Install in development mode
git clone https://github.com/dremok/oubli.git
cd oubli
pip install -e .
oubli setup

# Diagnose installation issues
oubli doctor

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
3. **Publish** (token stored at `~/.config/pypi/token`):
   ```bash
   TWINE_USERNAME=__token__ TWINE_PASSWORD=$(cat ~/.config/pypi/token) python -m twine upload dist/*
   ```
4. **Push** to GitHub: `git push`
5. **Confirm** with PyPI URL: `https://pypi.org/project/oubli/<version>/`

User can then upgrade in other projects: `pip install --upgrade oubli && oubli setup`

## Data Storage

User data is stored in `~/.oubli/`:
- `memories.lance/` - LanceDB database
- `core_memory.md` - Core Memory file (~2K tokens, always loaded)
