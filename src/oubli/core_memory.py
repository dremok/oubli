"""Core memory file operations for Oubli.

Core memory is a ~2K token markdown file that contains the most important
information about the user, always loaded at session start.
"""

from pathlib import Path
from typing import Optional

from .config import resolve_data_dir


CORE_MEMORY_FILENAME = "core_memory.md"


def get_core_memory_path(data_dir: Optional[Path] = None, auto_resolve: bool = True) -> Path:
    """Get the path to the core memory file.

    Args:
        data_dir: Explicit data directory. If None, auto-resolves.
        auto_resolve: If True and data_dir is None, check for local .oubli/
                     first, then fall back to global ~/.oubli/.
    """
    if data_dir:
        data_dir = Path(data_dir)
    elif auto_resolve:
        data_dir = resolve_data_dir(prefer_local=True)
    else:
        from .config import get_global_data_dir
        data_dir = get_global_data_dir()
    return data_dir / CORE_MEMORY_FILENAME


def load_core_memory(data_dir: Optional[Path] = None, auto_resolve: bool = True) -> str:
    """Load core memory content from file.

    Args:
        data_dir: Explicit data directory. If None, auto-resolves.
        auto_resolve: If True, check for local .oubli/ first.

    Returns:
        The core memory content, or empty string if file doesn't exist.
    """
    path = get_core_memory_path(data_dir, auto_resolve)
    if not path.exists():
        return ""
    return path.read_text()


def save_core_memory(content: str, data_dir: Optional[Path] = None, auto_resolve: bool = True) -> None:
    """Save core memory content to file.

    Args:
        content: The markdown content to save.
        data_dir: Optional custom data directory.
        auto_resolve: If True, check for local .oubli/ first.
    """
    if data_dir:
        data_dir = Path(data_dir)
    elif auto_resolve:
        data_dir = resolve_data_dir(prefer_local=True)
    else:
        from .config import get_global_data_dir
        data_dir = get_global_data_dir()

    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / CORE_MEMORY_FILENAME
    path.write_text(content)


def core_memory_exists(data_dir: Optional[Path] = None, auto_resolve: bool = True) -> bool:
    """Check if core memory file exists.

    Args:
        data_dir: Explicit data directory. If None, auto-resolves.
        auto_resolve: If True, check for local .oubli/ first.
    """
    return get_core_memory_path(data_dir, auto_resolve).exists()
