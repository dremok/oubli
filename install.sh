#!/bin/bash
set -e

# Oubli Installation Script
# Installs the fractal memory system for Claude Code

echo "Installing Oubli - Fractal Memory System for Claude Code"
echo "========================================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check for claude
if ! command -v claude &> /dev/null; then
    echo "Error: Claude Code CLI is required but not installed."
    echo "Install it from: https://claude.ai/code"
    exit 1
fi

echo ""
echo "1. Creating virtual environment..."
uv venv .venv

echo ""
echo "2. Installing dependencies..."
uv pip install -e .

echo ""
echo "3. Registering MCP server with Claude Code..."
claude mcp add oubli -- "$SCRIPT_DIR/.venv/bin/python" -m oubli.mcp_server || echo "   (MCP server already registered, continuing...)"

echo ""
echo "4. Setting up hooks in ~/.claude/settings.json..."
# Create ~/.claude if it doesn't exist
mkdir -p ~/.claude

# Create or update settings.json with our hooks
cat > /tmp/oubli_hooks.json << 'HOOKS'
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "INSTALL_PATH_PLACEHOLDER/.venv/bin/python -m oubli.cli inject-context"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Context compaction imminent. Silently save any memory-worthy information (preferences, personal facts, decisions, technical patterns) using memory_save. Do not announce or narrate - just save and continue."
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Silently save any memory-worthy information from this conversation (preferences, personal facts, decisions). If fundamental user info was revealed, update Core Memory. Do not announce or narrate - just save. If nothing to save, say nothing."
          }
        ]
      }
    ]
  }
}
HOOKS
# Replace placeholder with actual path
sed -i.bak "s|INSTALL_PATH_PLACEHOLDER|$SCRIPT_DIR|g" /tmp/oubli_hooks.json
rm -f /tmp/oubli_hooks.json.bak

# If settings.json exists, we need to merge; otherwise just copy
if [ -f ~/.claude/settings.json ]; then
    echo "   Note: ~/.claude/settings.json exists. Backing up to settings.json.bak"
    cp ~/.claude/settings.json ~/.claude/settings.json.bak
fi
cp /tmp/oubli_hooks.json ~/.claude/settings.json
rm /tmp/oubli_hooks.json

echo ""
echo "5. Creating data directory..."
mkdir -p ~/.oubli

echo ""
echo "========================================================="
echo "Installation complete!"
echo ""
echo "To use Oubli:"
echo "  1. Restart Claude Code"
echo "  2. Start chatting - Core Memory will be injected automatically"
echo "  3. Import existing memories: paste your Claude.ai export and ask to import"
echo ""
echo "Slash commands available:"
echo "  /clear-memories  - Clear all memories (requires confirmation)"
echo ""
echo "Data is stored in: ~/.oubli/"
echo "========================================================="
