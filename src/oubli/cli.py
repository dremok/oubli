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


def get_mcp_config(project_dir: Path) -> dict:
    """Generate .mcp.json content for local MCP server registration."""
    return {
        "mcpServers": {
            "oubli": {
                "command": "python",
                "args": ["-m", "oubli.mcp_server"],
                "cwd": str(project_dir)
            }
        }
    }


@main.command()
@click.option("--global", "install_global", is_flag=True,
              help="Install globally instead of project-local (default: local)")
def setup(install_global):
    """Set up Oubli for Claude Code.

    By default, installs everything locally in the current project:
    - .mcp.json (MCP server registration)
    - .claude/settings.local.json (hooks)
    - .claude/commands/ (slash commands)
    - .claude/CLAUDE.md (instructions)
    - .oubli/ (data directory)

    Use --global to install globally instead (MCP server, commands, instructions
    in ~/.claude/, data in ~/.oubli/).
    """
    project_dir = Path.cwd()
    data_path = get_package_data_path()

    if install_global:
        claude_dir = Path.home() / ".claude"
        oubli_dir = Path.home() / ".oubli"
        scope = "global"
    else:
        claude_dir = project_dir / ".claude"
        oubli_dir = project_dir / ".oubli"
        scope = "local"

    version = get_version()
    click.echo(f"Setting up Oubli v{version} - Fractal Memory System for Claude Code")
    click.echo(f"Installation scope: {scope}")
    click.echo("=" * 60)

    # 1. Register MCP server
    click.echo("\n1. Registering MCP server...")
    if install_global:
        # Global: use claude mcp add
        result = subprocess.run(
            ["claude", "mcp", "add", "oubli", "--", "python", "-m", "oubli.mcp_server"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo("   MCP server registered globally via 'claude mcp add'")
        else:
            click.echo("   MCP server already registered or error occurred")
    else:
        # Local: create .mcp.json
        mcp_config_path = project_dir / ".mcp.json"
        mcp_config = get_mcp_config(project_dir)

        if mcp_config_path.exists():
            # Merge with existing
            with open(mcp_config_path) as f:
                existing = json.load(f)
            if "mcpServers" not in existing:
                existing["mcpServers"] = {}
            existing["mcpServers"]["oubli"] = mcp_config["mcpServers"]["oubli"]
            mcp_config = existing

        with open(mcp_config_path, "w") as f:
            json.dump(mcp_config, f, indent=2)
        click.echo(f"   MCP server configured in .mcp.json")

    # 2. Set up hooks
    click.echo("\n2. Setting up hooks...")
    claude_dir.mkdir(exist_ok=True)

    if install_global:
        settings_path = claude_dir / "settings.json"
        if settings_path.exists():
            click.echo("   Backing up existing settings.json")
            shutil.copy(settings_path, claude_dir / "settings.json.bak")
        with open(settings_path, "w") as f:
            json.dump(HOOKS_CONFIG, f, indent=2)
        click.echo("   Hooks configured in ~/.claude/settings.json")
    else:
        settings_path = claude_dir / "settings.local.json"
        if settings_path.exists():
            with open(settings_path) as f:
                existing = json.load(f)
            if "hooks" not in existing:
                existing["hooks"] = {}
            existing["hooks"].update(HOOKS_CONFIG["hooks"])
            with open(settings_path, "w") as f:
                json.dump(existing, f, indent=2)
            click.echo("   Hooks merged into .claude/settings.local.json")
        else:
            with open(settings_path, "w") as f:
                json.dump(HOOKS_CONFIG, f, indent=2)
            click.echo("   Hooks configured in .claude/settings.local.json")

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
        click.echo(f"   CLAUDE.md installed to {claude_dir}/")
    else:
        click.echo("   Warning: CLAUDE.md not found in package data")

    # 5. Create data directory
    click.echo("\n5. Creating data directory...")
    oubli_dir.mkdir(exist_ok=True)
    click.echo(f"   Data directory: {oubli_dir}")

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("Setup complete!")
    click.echo(f"\nInstallation type: {scope.upper()}")
    click.echo("\nWhat was installed:")
    if install_global:
        click.echo("  - MCP server: registered via 'claude mcp add'")
    else:
        click.echo("  - MCP server: .mcp.json")
    click.echo("  - Hooks: UserPromptSubmit, PreCompact, Stop")
    click.echo("  - Slash commands: /clear-memories, /synthesize, /visualize-memory")
    click.echo(f"  - Instructions: {claude_dir}/CLAUDE.md")
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
@click.option("--global", "uninstall_global", is_flag=True,
              help="Uninstall global installation instead of local")
def uninstall(uninstall_global):
    """Remove Oubli from Claude Code.

    By default, removes local installation from current project:
    - .mcp.json (removes oubli entry)
    - .claude/settings.local.json (removes hooks)
    - .claude/commands/ (removes slash commands)
    - .claude/CLAUDE.md

    Use --global to remove global installation instead.

    Note: Data (.oubli/) is NOT deleted to preserve your memories.
    """
    project_dir = Path.cwd()

    if uninstall_global:
        claude_dir = Path.home() / ".claude"
        oubli_dir = Path.home() / ".oubli"
        scope = "global"
    else:
        claude_dir = project_dir / ".claude"
        oubli_dir = project_dir / ".oubli"
        scope = "local"

    click.echo(f"Uninstalling Oubli ({scope})")
    click.echo("=" * 40)

    # 1. Remove MCP server
    click.echo("\n1. Removing MCP server...")
    if uninstall_global:
        result = subprocess.run(
            ["claude", "mcp", "remove", "oubli"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo("   MCP server removed from global registry")
        else:
            click.echo("   MCP server not found or error occurred")
    else:
        mcp_config_path = project_dir / ".mcp.json"
        if mcp_config_path.exists():
            with open(mcp_config_path) as f:
                config = json.load(f)
            if "mcpServers" in config and "oubli" in config["mcpServers"]:
                del config["mcpServers"]["oubli"]
                if config["mcpServers"]:
                    with open(mcp_config_path, "w") as f:
                        json.dump(config, f, indent=2)
                else:
                    mcp_config_path.unlink()
                click.echo("   Oubli removed from .mcp.json")
            else:
                click.echo("   Oubli not found in .mcp.json")
        else:
            click.echo("   No .mcp.json found")

    # 2. Remove hooks
    click.echo("\n2. Removing hooks...")
    if uninstall_global:
        settings_path = claude_dir / "settings.json"
    else:
        settings_path = claude_dir / "settings.local.json"

    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)

        if "hooks" in settings:
            hooks_removed = []
            for hook_name in ["UserPromptSubmit", "PreCompact", "Stop"]:
                if hook_name in settings["hooks"]:
                    del settings["hooks"][hook_name]
                    hooks_removed.append(hook_name)

            if hooks_removed:
                with open(settings_path, "w") as f:
                    json.dump(settings, f, indent=2)
                click.echo(f"   Removed hooks: {', '.join(hooks_removed)}")
            else:
                click.echo("   No Oubli hooks found")
        else:
            click.echo("   No hooks found in settings")
    else:
        click.echo(f"   No {settings_path.name} found")

    # 3. Remove slash commands
    click.echo("\n3. Removing slash commands...")
    commands_dir = claude_dir / "commands"
    oubli_commands = ["clear-memories.md", "synthesize.md", "visualize-memory.md"]
    for cmd_name in oubli_commands:
        command_path = commands_dir / cmd_name
        if command_path.exists():
            command_path.unlink()
            click.echo(f"   /{cmd_name.replace('.md', '')} removed")

    # 4. Remove CLAUDE.md
    click.echo("\n4. Removing CLAUDE.md...")
    claude_md_path = claude_dir / "CLAUDE.md"
    if claude_md_path.exists():
        claude_md_path.unlink()
        click.echo("   CLAUDE.md removed")
    else:
        click.echo("   CLAUDE.md not found")

    # Summary
    click.echo("\n" + "=" * 40)
    click.echo("Uninstall complete!")
    click.echo(f"\nNote: Your memories in {oubli_dir}/ were NOT deleted.")
    click.echo(f"To remove all data: rm -rf {oubli_dir}/")
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
