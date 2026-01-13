"""Configuration and data directory resolution for Oubli.

Oubli can run in two modes:
- Local (default): Data stored in .oubli/ in the project directory
- Global: Data stored in ~/.oubli/

The MCP server and CLI commands detect which mode to use by checking
for the presence of a local .oubli/ directory.
"""

import os
from pathlib import Path
from typing import Optional


# Directory names
OUBLI_DIR_NAME = ".oubli"
CLAUDE_DIR_NAME = ".claude"
MCP_CONFIG_NAME = ".mcp.json"


def get_global_data_dir() -> Path:
    """Get the global data directory (~/.oubli/)."""
    return Path.home() / OUBLI_DIR_NAME


def get_local_data_dir(project_dir: Optional[Path] = None) -> Path:
    """Get the local data directory (.oubli/ in project).

    Args:
        project_dir: Project directory. Defaults to current working directory.
    """
    project_dir = Path(project_dir) if project_dir else Path.cwd()
    return project_dir / OUBLI_DIR_NAME


def find_project_root(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find the project root by looking for .oubli/ directory.

    Walks up from start_dir looking for a directory containing .oubli/.
    Stops at home directory or filesystem root.

    Args:
        start_dir: Directory to start searching from. Defaults to cwd.

    Returns:
        Path to project root if found, None otherwise.
    """
    current = Path(start_dir) if start_dir else Path.cwd()
    home = Path.home()

    while current != current.parent:  # Stop at filesystem root
        if current == home:
            # Don't go above home directory
            break
        if (current / OUBLI_DIR_NAME).exists():
            return current
        current = current.parent

    # Check home directory itself (for global installation marker)
    if (home / OUBLI_DIR_NAME).exists():
        return None  # Global mode, not a project root

    return None


def resolve_data_dir(prefer_local: bool = True) -> Path:
    """Resolve which data directory to use.

    Resolution order when prefer_local=True:
    1. Local .oubli/ in current directory or parent directories
    2. Global ~/.oubli/ if exists
    3. Local .oubli/ in current directory (for new installations)

    Args:
        prefer_local: If True, prefer local data directory.

    Returns:
        Path to the data directory to use.
    """
    if not prefer_local:
        return get_global_data_dir()

    # Check for local .oubli/ in current or parent directories
    project_root = find_project_root()
    if project_root:
        return project_root / OUBLI_DIR_NAME

    # Check if global exists
    global_dir = get_global_data_dir()
    if global_dir.exists():
        return global_dir

    # Default to local in current directory
    return get_local_data_dir()


def is_local_installation(data_dir: Optional[Path] = None) -> bool:
    """Check if using a local (project-specific) installation.

    Args:
        data_dir: Data directory to check. If None, resolves automatically.

    Returns:
        True if using local installation, False if global.
    """
    if data_dir is None:
        data_dir = resolve_data_dir()
    return data_dir != get_global_data_dir()


def get_claude_dir(local: bool = True, project_dir: Optional[Path] = None) -> Path:
    """Get the Claude configuration directory.

    Args:
        local: If True, return project-local .claude/ directory.
        project_dir: Project directory for local mode.

    Returns:
        Path to .claude/ directory.
    """
    if local:
        project_dir = Path(project_dir) if project_dir else Path.cwd()
        return project_dir / CLAUDE_DIR_NAME
    return Path.home() / CLAUDE_DIR_NAME


def get_mcp_config_path(project_dir: Optional[Path] = None) -> Path:
    """Get the path to .mcp.json for local MCP server registration.

    Args:
        project_dir: Project directory. Defaults to cwd.

    Returns:
        Path to .mcp.json file.
    """
    project_dir = Path(project_dir) if project_dir else Path.cwd()
    return project_dir / MCP_CONFIG_NAME
