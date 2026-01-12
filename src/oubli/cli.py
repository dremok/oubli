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


@click.group()
def main():
    """Oubli - Fractal memory system for Claude Code"""
    pass


@main.command()
def setup():
    """Set up Oubli for Claude Code.

    This command:
    1. Registers the MCP server with Claude Code
    2. Sets up hooks in ~/.claude/settings.json
    3. Installs slash commands
    4. Installs CLAUDE.md instructions
    5. Creates the data directory
    """
    claude_dir = Path.home() / ".claude"
    oubli_dir = Path.home() / ".oubli"
    data_path = get_package_data_path()

    click.echo("Setting up Oubli - Fractal Memory System for Claude Code")
    click.echo("=" * 55)

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
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.json"

    if settings_path.exists():
        click.echo("   Backing up existing settings.json")
        shutil.copy(settings_path, claude_dir / "settings.json.bak")

    with open(settings_path, "w") as f:
        json.dump(HOOKS_CONFIG, f, indent=2)
    click.echo("   Hooks configured in ~/.claude/settings.json")

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
    click.echo("  - Hooks: UserPromptSubmit, PreCompact, Stop")
    click.echo("  - Slash commands: /clear-memories, /synthesize")
    click.echo("  - Instructions: ~/.claude/CLAUDE.md")
    click.echo(f"  - Data directory: {oubli_dir}")
    click.echo("\nRestart Claude Code to start using Oubli.")


@main.command()
def uninstall():
    """Remove Oubli from Claude Code.

    This command:
    1. Removes the MCP server registration
    2. Removes hooks from settings.json
    3. Removes slash commands
    4. Removes CLAUDE.md

    Note: Data in ~/.oubli/ is NOT deleted (your memories are preserved).
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

    # 2. Remove hooks (restore backup if exists)
    click.echo("\n2. Removing hooks...")
    settings_path = claude_dir / "settings.json"
    backup_path = claude_dir / "settings.json.bak"

    if backup_path.exists():
        shutil.copy(backup_path, settings_path)
        backup_path.unlink()
        click.echo("   Restored settings.json from backup")
    elif settings_path.exists():
        settings_path.unlink()
        click.echo("   Removed settings.json")

    # 3. Remove slash commands
    click.echo("\n3. Removing slash commands...")
    oubli_commands = ["clear-memories.md", "synthesize.md"]
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
    click.echo("To completely remove all data, run: rm -rf ~/.oubli/")
    click.echo("\nTo fully uninstall the package: pip uninstall oubli")


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


if __name__ == "__main__":
    main()
