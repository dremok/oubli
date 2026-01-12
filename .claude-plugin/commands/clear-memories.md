---
description: Clear all memories from the Oubli database
allowed-tools: Bash
---

# Clear Memories

Clear all memories from the Oubli memory database. This is destructive and cannot be undone.

Steps:
1. Ask the user to confirm they want to delete ALL memories
2. If confirmed, run: `rm -rf ~/.oubli/memories.lance`
3. Report success

Note: This only clears the memories database, not the core memory file (~/.oubli/core_memory.md).
