# Synthesize Memories

Consolidate raw memories into higher-level insights and update Core Memory.

**When to run:** After accumulating many raw memories (10+), or when you notice duplicate/overlapping memories.

## Workflow

Execute silently (no step-by-step narration):

```
current_level = 0

LOOP:
  1. Call memory_prepare_synthesis(level=current_level)
     - This auto-merges duplicates (85% similarity threshold)
     - Returns topic groups ready for synthesis

  2. If no groups or < 2 memories remaining:
     - GOTO FINAL STEP

  3. For each group:
     - Read all summaries in the group
     - Create a 1-2 sentence insight capturing the pattern
     - Call memory_synthesize(
         parent_ids=[IDs from group],
         summary="your insight",
         topics=[topic],
         delete_parents=false
       )

  4. current_level += 1
  5. GOTO LOOP

FINAL STEP - Update Core Memory:
  1. Get highest-level insights via memory_list(level=highest)
  2. Get current Core Memory via core_memory_get()
  3. Regenerate Core Memory:
     - Keep stable identity (name, family, location)
     - Update sections with new insights
     - Keep concise (~2K tokens max)
     - Maintain markdown structure
  4. Save via core_memory_save(content)
```

## Output

When complete, provide a brief summary:
- Levels processed
- Duplicates merged
- Syntheses created
- Core Memory updated: yes/no

Do NOT narrate each step - just do it and report the final result.
