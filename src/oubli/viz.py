"""Memory graph visualization using vis.js with custom HTML rendering."""

import json
import webbrowser
from collections import defaultdict
from pathlib import Path

from .storage import MemoryStore, Memory


# Color scheme by level
LEVEL_COLORS = {
    0: "#4A90D9",  # Blue - raw memories
    1: "#50C878",  # Green - first synthesis
    2: "#9B59B6",  # Purple - higher synthesis
}
DEFAULT_COLOR = "#9B59B6"  # Purple for level 3+

# Topic colors (generated dynamically)
TOPIC_COLORS = [
    "#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6",
    "#1ABC9C", "#E67E22", "#34495E", "#16A085", "#C0392B",
]


def extract_short_label(summary: str, max_words: int = 3) -> str:
    """Extract 1-3 word label from summary."""
    words = summary.split()[:max_words]
    label = " ".join(words)
    if len(summary.split()) > max_words:
        label += "..."
    return label


def level_color(level: int) -> str:
    """Get color for memory level."""
    return LEVEL_COLORS.get(level, DEFAULT_COLOR)


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def build_graph_data(memories: list[Memory]) -> dict:
    """Build nodes and edges data for vis.js."""
    memory_map = {m.id: m for m in memories}

    nodes = []
    edges = []

    for memory in memories:
        topics = ", ".join(memory.topics) if memory.topics else "none"
        keywords = ", ".join(memory.keywords) if memory.keywords else "none"
        level_text = "raw" if memory.level == 0 else "synthesized"

        nodes.append({
            "id": memory.id,
            "label": extract_short_label(memory.summary),
            "color": level_color(memory.level),
            "level": memory.level,
            "size": 25 + (memory.level * 5),
            # Store data for custom tooltip
            "summary": escape_html(memory.summary),
            "levelNum": memory.level,
            "levelText": level_text,
            "topics": escape_html(topics),
            "topicsList": memory.topics,
            "keywords": escape_html(keywords),
            "source": memory.source or "unknown",
        })

        for parent_id in memory.parent_ids:
            if parent_id in memory_map:
                edges.append({"from": parent_id, "to": memory.id})

    return {"nodes": nodes, "edges": edges}


def collect_topics(memories: list[Memory]) -> dict:
    """Collect all topics with their memory counts."""
    topic_counts = defaultdict(int)
    for memory in memories:
        for topic in memory.topics:
            topic_counts[topic] += 1
    return dict(sorted(topic_counts.items(), key=lambda x: -x[1]))


def generate_html(output_path: Path, memories: list[Memory]) -> Path:
    """Generate HTML visualization with topic navigation."""
    if not memories:
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Oubli Memory Graph</title>
    <style>
        body { font-family: system-ui; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
        .empty { text-align: center; color: #666; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <div class="empty">
        <h1>No Memories Yet</h1>
        <p>Start a conversation with Claude to save memories.</p>
    </div>
</body>
</html>"""
        output_path.write_text(html_content)
        return output_path

    graph_data = build_graph_data(memories)
    topics = collect_topics(memories)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Oubli Memory Graph</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" />
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 0;
            background: #f8f9fa;
        }}
        .container {{
            display: flex;
            height: 100vh;
        }}
        .sidebar {{
            width: 220px;
            background: #fff;
            border-right: 1px solid #e0e0e0;
            padding: 20px;
            overflow-y: auto;
        }}
        .sidebar h2 {{
            margin: 0 0 15px 0;
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .topic-btn {{
            display: block;
            width: 100%;
            padding: 10px 12px;
            margin-bottom: 8px;
            border: none;
            border-radius: 6px;
            background: #f0f0f0;
            color: #333;
            font-size: 13px;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s;
        }}
        .topic-btn:hover {{
            background: #e0e0e0;
        }}
        .topic-btn.active {{
            background: #4A90D9;
            color: white;
        }}
        .topic-btn .count {{
            float: right;
            background: rgba(0,0,0,0.1);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
        }}
        .topic-btn.active .count {{
            background: rgba(255,255,255,0.2);
        }}
        .main {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        .header {{
            padding: 15px 20px;
            background: #fff;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 18px;
            color: #333;
        }}
        .legend {{
            display: flex;
            gap: 15px;
            margin-left: auto;
            font-size: 12px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        #graph {{
            flex: 1;
            background: #fff;
            min-height: 600px;
            height: calc(100vh - 60px);
        }}
        #tooltip {{
            position: absolute;
            padding: 12px 16px;
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-width: 350px;
            font-size: 13px;
            line-height: 1.5;
            display: none;
            z-index: 1000;
            pointer-events: none;
        }}
        #tooltip strong {{
            color: #666;
            font-weight: 500;
        }}
        #tooltip .summary {{
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
        }}
        #tooltip .row {{
            margin: 4px 0;
        }}
        .stats {{
            font-size: 12px;
            color: #888;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h2>Topics</h2>
            <button class="topic-btn active" data-topic="all">
                All Memories <span class="count">{len(memories)}</span>
            </button>
            {"".join(f'<button class="topic-btn" data-topic="{topic}">{topic} <span class="count">{count}</span></button>' for topic, count in topics.items())}
        </div>
        <div class="main">
            <div class="header">
                <h1>Oubli Memory Graph</h1>
                <span class="stats" id="stats">Showing {len(memories)} memories</span>
                <div class="legend">
                    <div class="legend-item"><div class="legend-dot" style="background: #4A90D9"></div> Level 0 (raw)</div>
                    <div class="legend-item"><div class="legend-dot" style="background: #50C878"></div> Level 1</div>
                    <div class="legend-item"><div class="legend-dot" style="background: #9B59B6"></div> Level 2+</div>
                </div>
            </div>
            <div id="graph"></div>
        </div>
    </div>
    <div id="tooltip"></div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {{
        const allData = {json.dumps(graph_data)};

        const container = document.getElementById('graph');
        const tooltip = document.getElementById('tooltip');
        const stats = document.getElementById('stats');

        if (!container) {{
            console.error('Graph container not found');
            return;
        }}

        const options = {{
            nodes: {{
                font: {{ size: 14, color: '#333' }},
                borderWidth: 2,
                shape: 'dot'
            }},
            edges: {{
                arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
                color: {{ color: '#888888' }},
                smooth: {{ type: 'cubicBezier' }}
            }},
            physics: {{
                enabled: true,
                hierarchicalRepulsion: {{
                    centralGravity: 0.0,
                    springLength: 150,
                    springConstant: 0.01,
                    nodeDistance: 200
                }},
                solver: 'hierarchicalRepulsion'
            }},
            layout: {{
                hierarchical: {{
                    enabled: true,
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 150,
                    nodeSpacing: 200
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 0
            }}
        }};

        let network = null;
        let currentTopic = 'all';

        function filterByTopic(topic) {{
            let filteredNodes, filteredEdges;

            if (topic === 'all') {{
                filteredNodes = allData.nodes;
                filteredEdges = allData.edges;
            }} else {{
                const nodeIds = new Set();
                filteredNodes = allData.nodes.filter(n => {{
                    if (n.topicsList && n.topicsList.includes(topic)) {{
                        nodeIds.add(n.id);
                        return true;
                    }}
                    return false;
                }});
                filteredEdges = allData.edges.filter(e =>
                    nodeIds.has(e.from) && nodeIds.has(e.to)
                );
            }}

            stats.textContent = `Showing ${{filteredNodes.length}} memories`;

            const data = {{
                nodes: new vis.DataSet(filteredNodes),
                edges: new vis.DataSet(filteredEdges)
            }};

            if (network) {{
                network.destroy();
            }}
            network = new vis.Network(container, data, options);

            // Custom tooltip on hover
            network.on('hoverNode', function(params) {{
                const node = filteredNodes.find(n => n.id === params.node);
                if (node) {{
                    tooltip.innerHTML = `
                        <div class="summary">${{node.summary}}</div>
                        <div class="row"><strong>Level:</strong> ${{node.levelNum}} (${{node.levelText}})</div>
                        <div class="row"><strong>Topics:</strong> ${{node.topics}}</div>
                        <div class="row"><strong>Keywords:</strong> ${{node.keywords}}</div>
                        <div class="row"><strong>Source:</strong> ${{node.source}}</div>
                    `;
                    tooltip.style.display = 'block';
                }}
            }});

            network.on('blurNode', function() {{
                tooltip.style.display = 'none';
            }});

            // Position tooltip near cursor
            container.addEventListener('mousemove', function(e) {{
                if (tooltip.style.display === 'block') {{
                    const x = e.clientX + 15;
                    const y = e.clientY + 15;
                    // Keep tooltip in viewport
                    const maxX = window.innerWidth - tooltip.offsetWidth - 20;
                    const maxY = window.innerHeight - tooltip.offsetHeight - 20;
                    tooltip.style.left = Math.min(x, maxX) + 'px';
                    tooltip.style.top = Math.min(y, maxY) + 'px';
                }}
            }});
        }}

        // Topic button handlers
        document.querySelectorAll('.topic-btn').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.topic-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                filterByTopic(this.dataset.topic);
            }});
        }});

        // Initial render
        try {{
            filterByTopic('all');
        }} catch (e) {{
            console.error('Error initializing graph:', e);
            document.getElementById('graph').innerHTML = '<p style="padding:20px;color:red;">Error loading graph: ' + e.message + '</p>';
        }}
        }}); // end DOMContentLoaded
    </script>
</body>
</html>"""

    output_path.write_text(html_content)
    return output_path


def visualize(output_path: Path = None, open_browser: bool = True) -> Path:
    """Generate and optionally open memory graph visualization.

    Args:
        output_path: Where to save HTML file. Defaults to data_dir/graph.html
        open_browser: Whether to open the file in default browser

    Returns:
        Path to generated HTML file
    """
    from .config import resolve_data_dir

    if output_path is None:
        data_dir = resolve_data_dir(prefer_local=True)
        output_path = data_dir / "graph.html"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load memories
    store = MemoryStore()
    memories = store.get_all()

    # Generate HTML
    generate_html(output_path, memories)

    # Open in browser
    if open_browser:
        webbrowser.open(f"file://{output_path.absolute()}")

    return output_path
