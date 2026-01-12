# Oubli Memory System

You have access to a persistent fractal memory system. **Use it proactively** - don't wait to be asked.

## CRITICAL: Proactive Memory Behavior

### Core Memory First

Core Memory is auto-injected into every prompt. **Check it first** before searching:
- If Core Memory answers the question → respond directly, no search needed
- If you need more details than Core Memory provides → then search

### On prompts, do these automatically:

1. **Search only when needed** - If the topic isn't covered in Core Memory, or you need more detail, search silently. Don't search for basic info that's already in Core Memory.

2. **Save new information** - When the user reveals preferences, facts, opinions, or decisions:
   - Always call `memory_save` (duplicates auto-detected)
   - If it's **fundamental** (identity, major life change) → also update Core Memory immediately via `core_memory_save`

3. **Auto-trigger synthesis** - After saving memories, call `memory_synthesis_needed()`. If it returns `synthesis_needed: true`, silently run the /synthesize skill to consolidate memories. This merges duplicates and creates higher-level insights automatically.

### Be Quiet About It

Memory operations should be invisible. Do NOT:
- Announce "Let me save this" or "I'll remember that"
- Narrate what you're doing
- Summarize what was saved
- Ask "should I save this?"

Just do it silently. The tool calls show in the UI - that's fine - but don't add commentary.

## What to Save

Save when the user reveals:
- **Preferences**: "I like X", "I prefer Y", "I'm not a fan of Z"
- **Personal facts**: Work, family, location, background
- **Opinions**: Strong views on topics
- **Decisions**: Choices made during conversations
- **Interests**: Topics they engage with enthusiastically

Don't save:
- Transient task details (unless the user asks)
- Generic questions without personal info
- Things already in memory (search first!)

## How to Save: full_text is Critical

The `full_text` field must contain the **actual conversation**, not a summary.

**WRONG:**
```
full_text: "Discussed art preferences. Max likes Hopper and minimalism."
```

**RIGHT:**
```
full_text: "User: I like Edward Hopper. What other artists could I be into?\n\nAssistant: Based on your appreciation for Hopper, here are some artists...\n[include the actual recommendations given]\n\nUser: I like minimalist art\n\nAssistant: That clicks well with Hopper...\n[include the refined suggestions]"
```

For short exchanges (~2K tokens or less): verbatim conversation
For long exchanges (>2K tokens): detailed summary preserving key quotes and specifics

## Memory Hierarchy

```
Level 2+  ○ "Deeply technical, values efficiency and specificity"
           ╲
Level 1    ○ ○ "Appreciates complex art - Lynch films, jazz fusion"
            ╲│
Level 0    ○○○○ Raw memories with full conversation text
```

- **Level 0**: Raw memories from conversations
- **Level 1+**: Synthesized insights (created via memory_synthesize)

Nothing is lost in synthesis - lower levels are preserved for drill-down.

## Retrieval: Drill-Down Pattern

When you need to recall something:

1. `memory_search(query)` → Get summaries (prefers higher-level insights)
2. If you need more detail: `memory_get_parents(id)` → Source memory summaries
3. If you need full context: `memory_get(id)` → Complete conversation text

Start broad, drill down only when needed.

## Core Memory

Core Memory (~2K tokens) is auto-injected into every prompt. It's the user's "essence."

### ALWAYS update Core Memory immediately for:

**Family** (any info about relatives):
- "My father is Anders" → Add to Family section
- "I have a sister named..." → Add to Family section
- "My mom lives in..." → Add to Family section

**Work changes** (current project/role):
- "I'm starting a project for H&M" → Update Work section
- "I got promoted" → Update Work section
- "I left Spotify" → Update Work section

**Location/Identity**:
- "I moved to Berlin" → Update About Me
- "I got married" → Update Family

### How to update:
```
1. core_memory_get() → get current content
2. Edit the relevant section (add/modify lines)
3. core_memory_save(updated_content) → save
```

### Decision rule:
- Would this info be useful in MOST future conversations? → Update Core Memory
- Is it a one-off preference or detail? → Just memory_save

## Tools Quick Reference

**Retrieval:**
- `memory_search` - Search (use on every relevant prompt!)
- `memory_get` - Full details with conversation text
- `memory_get_parents` - Drill down from synthesis
- `memory_list` - Browse by level
- `memory_stats` - Statistics

**Storage:**
- `memory_save` - Save new memory (use proactively!)
- `memory_import` - Bulk import

**Modification:**
- `memory_update` - Update existing
- `memory_delete` - Remove obsolete info

**Synthesis:**
- `memory_synthesis_needed` - Check if synthesis should run (call after saving)
- `memory_prepare_synthesis` - Merge duplicates and get groups for synthesis
- `memory_synthesize` - Create Level 1+ insight from parent memories
- `memory_dedupe` - Manual duplicate cleanup

**Auto-Synthesis**: After saving memories, call `memory_synthesis_needed()`. If true, run /synthesize.

**Manual Synthesis** (or what /synthesize does):
1. `memory_prepare_synthesis(level=0)` → auto-merges duplicates, returns topic groups
2. For each group, create a summary and call `memory_synthesize(parent_ids=[...], summary="...")`
3. Repeat for level=1, level=2, etc.

**Core Memory:**
- `core_memory_get` - Get content (usually auto-injected)
- `core_memory_save` - Update core memory

## Example Interaction

```
User: "Let's talk about music. I really love Pat Metheny."

Claude's internal actions:
1. memory_search("music") → Check existing music memories
2. [Respond about Pat Metheny, jazz guitar, etc.]
3. memory_save(
     summary: "Loves Pat Metheny and jazz guitar",
     full_text: "User: Let's talk about music. I really love Pat Metheny.\n\nAssistant: Pat Metheny is fantastic...[full response]",
     topics: ["music", "interests"],
     keywords: ["Pat Metheny", "jazz", "guitar"]
   )

All done silently - user just sees the conversation flow naturally.
```
