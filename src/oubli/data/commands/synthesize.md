# Synthesize Memories

Run the full memory synthesis workflow: merge duplicates, create higher-level insights, and update Core Memory.

## Instructions

Execute this workflow silently (no narration):

```
current_level = 0

LOOP:
  1. Call memory_prepare_synthesis(level=current_level)

  2. If duplicates_merged > 0:
     - Note: "Merged {n} duplicates at Level {current_level}"

  3. If synthesis_groups == 0 or memories_remaining < 2:
     - GOTO FINAL STEP

  4. For each group in groups:
     - Read all the summaries in that group
     - Create a 1-2 sentence insight that captures the pattern/theme
     - Call memory_synthesize(
         parent_ids=[list of IDs from group],
         summary="your insight",
         topics=[the topic],
         delete_parents=false
       )

  5. current_level += 1
  6. GOTO LOOP

FINAL STEP - Update Core Memory:
  1. Call memory_list(level=highest_level_reached) to get top-level insights
  2. Also get current core_memory_get() content
  3. Regenerate Core Memory by:
     - Keeping stable identity info (name, family, location)
     - Updating/adding insights from synthesis
     - Keeping it concise (~2K tokens max)
     - Maintaining markdown structure
  4. Call core_memory_save(content) with the updated content
```

## Output

When complete, provide a brief summary:
- Levels processed
- Total duplicates merged
- Syntheses created
- Core Memory updated: yes/no

Do NOT narrate each step - just do it and report the final result.
