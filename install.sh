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
claude mcp add oubli -- "$SCRIPT_DIR/.venv/bin/python" -m oubli.mcp_server

echo ""
echo "4. Updating plugin hooks with installation path..."
# Update hooks.json with the actual installation path
sed -i.bak "s|OUBLI_INSTALL_PATH|$SCRIPT_DIR|g" "$SCRIPT_DIR/.claude-plugin/hooks/hooks.json"
rm -f "$SCRIPT_DIR/.claude-plugin/hooks/hooks.json.bak"

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
