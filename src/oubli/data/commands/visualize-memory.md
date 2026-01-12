# Visualize Memory Graph

Open an interactive graph visualization of all memories in the browser.

## Instructions

Run the following command to generate and open the memory graph:

```bash
oubli viz
```

This opens `~/.oubli/graph.html` in your default browser showing:
- **Hierarchical tree** - Raw memories at top, synthesized insights below
- **Topic sidebar** - Filter by topic to focus on specific areas
- **Color coding** - Blue (L0 raw), Green (L1), Purple (L2+)
- **Tooltips** - Hover for full summary, topics, keywords

If the user wants to generate without opening:
```bash
oubli viz --no-open
```
