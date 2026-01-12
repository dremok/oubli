"""CLI commands for Oubli.

Provides command-line interface for setup, memory operations and session hooks.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import click

from .core_memory import load_core_memory, core_memory_exists
from .viz import visualize


# Hooks configuration
HOOKS_CONFIG = {
    "hooks": {
        "UserPromptSubmit": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python -m oubli.cli inject-context"
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


def get_package_data_path() -> Path:
    """Get the path to the package's data directory."""
    return Path(__file__).parent / "data"


def get_version() -> str:
    """Get package version."""
    try:
        from importlib.metadata import version
        return version("oubli")
    except Exception:
        return "unknown"


@click.group()
@click.version_option(get_version(), prog_name="oubli")
def main():
    """Oubli - Fractal memory system for Claude Code"""
    pass


@main.command()
@click.option("--global", "install_global", is_flag=True,
              help="Install hooks globally (default: project-local)")
def setup(install_global):
    """Set up Oubli for Claude Code.

    This command:
    1. Registers the MCP server with Claude Code (global)
    2. Sets up hooks (project-local by default, or global with --global)
    3. Installs slash commands (global)
    4. Installs CLAUDE.md instructions (global)
    5. Creates the data directory (global)
    """
    claude_dir = Path.home() / ".claude"
    oubli_dir = Path.home() / ".oubli"
    data_path = get_package_data_path()

    version = get_version()
    click.echo(f"Setting up Oubli v{version} - Fractal Memory System for Claude Code")
    click.echo("=" * 60)

    # 1. Register MCP server
    click.echo("\n1. Registering MCP server...")
    result = subprocess.run(
        ["claude", "mcp", "add", "oubli", "--", "python", "-m", "oubli.mcp_server"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        click.echo("   MCP server registered successfully")
    else:
        click.echo("   MCP server already registered or error occurred")

    # 2. Set up hooks
    click.echo("\n2. Setting up hooks...")
    if install_global:
        # Global installation
        claude_dir.mkdir(exist_ok=True)
        settings_path = claude_dir / "settings.json"

        if settings_path.exists():
            click.echo("   Backing up existing settings.json")
            shutil.copy(settings_path, claude_dir / "settings.json.bak")

        with open(settings_path, "w") as f:
            json.dump(HOOKS_CONFIG, f, indent=2)
        click.echo("   Hooks configured in ~/.claude/settings.json (global)")
    else:
        # Project-local installation
        local_claude_dir = Path.cwd() / ".claude"
        local_claude_dir.mkdir(exist_ok=True)
        local_settings_path = local_claude_dir / "settings.local.json"

        if local_settings_path.exists():
            # Merge with existing settings
            with open(local_settings_path) as f:
                existing = json.load(f)

            # Merge hooks
            if "hooks" not in existing:
                existing["hooks"] = {}
            existing["hooks"].update(HOOKS_CONFIG["hooks"])

            with open(local_settings_path, "w") as f:
                json.dump(existing, f, indent=2)
            click.echo("   Hooks merged into .claude/settings.local.json")
        else:
            with open(local_settings_path, "w") as f:
                json.dump(HOOKS_CONFIG, f, indent=2)
            click.echo("   Hooks configured in .claude/settings.local.json (project-local)")

    # 3. Install slash commands
    click.echo("\n3. Installing slash commands...")
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir(exist_ok=True)

    src_commands_dir = data_path / "commands"
    if src_commands_dir.exists():
        for cmd_file in src_commands_dir.glob("*.md"):
            shutil.copy(cmd_file, commands_dir / cmd_file.name)
            click.echo(f"   /{cmd_file.stem} command installed")
    else:
        click.echo("   Warning: commands directory not found in package data")

    # 4. Install CLAUDE.md
    click.echo("\n4. Installing CLAUDE.md...")
    src_claude_md = data_path / "CLAUDE.md"
    dst_claude_md = claude_dir / "CLAUDE.md"
    if src_claude_md.exists():
        shutil.copy(src_claude_md, dst_claude_md)
        click.echo("   CLAUDE.md installed to ~/.claude/")
    else:
        click.echo("   Warning: CLAUDE.md not found in package data")

    # 5. Create data directory
    click.echo("\n5. Creating data directory...")
    oubli_dir.mkdir(exist_ok=True)
    click.echo(f"   Data directory: {oubli_dir}")

    # Summary
    click.echo("\n" + "=" * 55)
    click.echo("Setup complete!")
    click.echo("\nWhat was installed:")
    click.echo("  - MCP server: oubli (15 memory tools)")
    hook_scope = "global" if install_global else "project-local"
    click.echo(f"  - Hooks: UserPromptSubmit, PreCompact, Stop ({hook_scope})")
    click.echo("  - Slash commands: /clear-memories, /synthesize, /visualize-memory")
    click.echo("  - Instructions: ~/.claude/CLAUDE.md")
    click.echo(f"  - Data directory: {oubli_dir}")
    click.echo("\nRestart Claude Code to start using Oubli.")


@main.command()
def enable():
    """Enable Oubli hooks for the current project.

    This adds Oubli hooks to .claude/settings.local.json in the current directory.
    Useful for adding Oubli to existing projects.
    """
    local_claude_dir = Path.cwd() / ".claude"
    local_claude_dir.mkdir(exist_ok=True)
    local_settings_path = local_claude_dir / "settings.local.json"

    click.echo("Enabling Oubli for current project")
    click.echo("=" * 40)

    if local_settings_path.exists():
        # Merge with existing settings
        with open(local_settings_path) as f:
            existing = json.load(f)

        # Merge hooks
        if "hooks" not in existing:
            existing["hooks"] = {}
        existing["hooks"].update(HOOKS_CONFIG["hooks"])

        with open(local_settings_path, "w") as f:
            json.dump(existing, f, indent=2)
        click.echo("✓ Hooks merged into .claude/settings.local.json")
    else:
        with open(local_settings_path, "w") as f:
            json.dump(HOOKS_CONFIG, f, indent=2)
        click.echo("✓ Hooks configured in .claude/settings.local.json")

    click.echo("\nOubli enabled for this project!")
    click.echo("Restart Claude Code to activate.")


@main.command()
def disable():
    """Disable Oubli hooks for the current project.

    This removes Oubli hooks from .claude/settings.local.json in the current directory.
    """
    local_settings_path = Path.cwd() / ".claude" / "settings.local.json"

    click.echo("Disabling Oubli for current project")
    click.echo("=" * 40)

    if not local_settings_path.exists():
        click.echo("No local settings found - Oubli not enabled for this project")
        return

    with open(local_settings_path) as f:
        settings = json.load(f)

    if "hooks" not in settings:
        click.echo("No hooks found in local settings")
        return

    # Remove Oubli hooks
    hooks_removed = []
    for hook_name in ["UserPromptSubmit", "PreCompact", "Stop"]:
        if hook_name in settings["hooks"]:
            del settings["hooks"][hook_name]
            hooks_removed.append(hook_name)

    if hooks_removed:
        with open(local_settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        click.echo(f"✓ Removed hooks: {', '.join(hooks_removed)}")
    else:
        click.echo("No Oubli hooks found to remove")

    click.echo("\nOubli disabled for this project!")


@main.command()
def remove_global_hooks():
    """Remove Oubli hooks from global settings.

    Use this to transition from global hooks to project-local hooks.
    This only removes hooks from ~/.claude/settings.json.
    """
    claude_dir = Path.home() / ".claude"
    settings_path = claude_dir / "settings.json"
    backup_path = claude_dir / "settings.json.bak"

    click.echo("Removing global Oubli hooks")
    click.echo("=" * 40)

    if not settings_path.exists():
        click.echo("No global settings.json found")
        return

    with open(settings_path) as f:
        settings = json.load(f)

    if "hooks" not in settings:
        click.echo("No hooks found in global settings")
        return

    # Backup current settings
    shutil.copy(settings_path, backup_path)
    click.echo(f"✓ Backed up to {backup_path}")

    # Remove Oubli hooks
    hooks_removed = []
    for hook_name in ["UserPromptSubmit", "PreCompact", "Stop"]:
        if hook_name in settings["hooks"]:
            del settings["hooks"][hook_name]
            hooks_removed.append(hook_name)

    if hooks_removed:
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        click.echo(f"✓ Removed hooks: {', '.join(hooks_removed)}")
    else:
        click.echo("No Oubli hooks found to remove")

    click.echo("\nGlobal hooks removed!")
    click.echo("Use 'oubli enable' in each project where you want Oubli.")


@main.command()
def uninstall():
    """Remove Oubli from Claude Code.

    This command:
    1. Removes the MCP server registration
    2. Removes global hooks from settings.json (if present)
    3. Removes slash commands
    4. Removes CLAUDE.md

    Note: Data in ~/.oubli/ is NOT deleted (your memories are preserved).
    Note: Project-local hooks (.claude/settings.local.json) are NOT removed.
    """
    claude_dir = Path.home() / ".claude"

    click.echo("Uninstalling Oubli from Claude Code")
    click.echo("=" * 40)

    # 1. Remove MCP server
    click.echo("\n1. Removing MCP server...")
    result = subprocess.run(
        ["claude", "mcp", "remove", "oubli"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        click.echo("   MCP server removed")
    else:
        click.echo("   MCP server not found or error occurred")

    # 2. Remove global hooks (but keep backup)
    click.echo("\n2. Removing global hooks...")
    settings_path = claude_dir / "settings.json"
    backup_path = claude_dir / "settings.json.bak"

    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)

        if "hooks" in settings:
            # Backup before removing
            shutil.copy(settings_path, backup_path)

            # Remove Oubli hooks
            for hook_name in ["UserPromptSubmit", "PreCompact", "Stop"]:
                if hook_name in settings["hooks"]:
                    del settings["hooks"][hook_name]

            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)
            click.echo("   Global hooks removed (backup saved)")
        else:
            click.echo("   No hooks found in global settings")
    else:
        click.echo("   No global settings.json found")

    # 3. Remove slash commands
    click.echo("\n3. Removing slash commands...")
    oubli_commands = ["clear-memories.md", "synthesize.md", "visualize-memory.md"]
    for cmd_name in oubli_commands:
        command_path = claude_dir / "commands" / cmd_name
        if command_path.exists():
            command_path.unlink()
            click.echo(f"   /{cmd_name.replace('.md', '')} command removed")

    # 4. Remove CLAUDE.md
    click.echo("\n4. Removing CLAUDE.md...")
    claude_md_path = claude_dir / "CLAUDE.md"
    if claude_md_path.exists():
        claude_md_path.unlink()
        click.echo("   CLAUDE.md removed")

    # Summary
    click.echo("\n" + "=" * 40)
    click.echo("Uninstall complete!")
    click.echo("\nNote: Your memories in ~/.oubli/ were NOT deleted.")
    click.echo("Note: Project-local hooks (.claude/settings.local.json) were NOT removed.")
    click.echo("      Use 'oubli disable' in each project to remove them.")
    click.echo("\nTo completely remove all data, run: rm -rf ~/.oubli/")
    click.echo("To fully uninstall the package: pip uninstall oubli")


@main.command("inject-context")
def inject_context():
    """Inject core memory into conversation (called by hooks)."""
    additional_context = ""

    if core_memory_exists():
        content = load_core_memory()
        if content:
            additional_context = f"# Core Memory\n\n{content}"

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context
        }
    }
    print(json.dumps(output))


@main.command("session-start")
def session_start():
    """Output core memory (legacy command)."""
    if not core_memory_exists():
        print("No core memory found. Use core_memory_save to create one.")
        return

    content = load_core_memory()
    if content:
        print("# Core Memory (loaded automatically)\n")
        print(content)
    else:
        print("Core memory file exists but is empty.")


@main.command()
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output path for HTML file (default: ~/.oubli/graph.html)")
@click.option("--no-open", is_flag=True, default=False,
              help="Generate file but don't open in browser")
def viz(output, no_open):
    """Visualize memory graph in browser.

    Opens an interactive graph showing all memories and their relationships.
    Nodes are colored by level (blue=raw, green=L1, purple=L2+).
    Hover over nodes to see full details.
    """
    from pathlib import Path

    output_path = Path(output) if output else None
    result_path = visualize(output_path=output_path, open_browser=not no_open)

    if no_open:
        click.echo(f"Graph saved to: {result_path}")
    else:
        click.echo(f"Opening graph: {result_path}")


if __name__ == "__main__":
    main()
