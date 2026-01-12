---
description: Clear all memories from the Oubli database
allowed-tools: Bash
---

# Clear Memories

Clear all memories from the Oubli memory database. This is destructive and cannot be undone.

## Steps

1. Ask the user to confirm: "This will permanently delete ALL memories. Core Memory will be preserved. Are you sure?"

2. If confirmed, run:
   ```bash
   python -c "from oubli.storage import MemoryStore; store = MemoryStore(); count = store.delete_all(); print(f'Deleted {count} memories')"
   ```

3. Report: "Deleted {n} memories. Core Memory (~/.oubli/core_memory.md) was preserved."

## Note

- Only clears the memories database, NOT Core Memory
- Core Memory can be manually edited at `~/.oubli/core_memory.md`
