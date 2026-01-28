"""CLI commands for Oubli.

Provides command-line interface for setup, memory operations and session hooks.

Architecture:
- Config files (.mcp.json, .claude/) are installed locally per project
- Data (~/.oubli/) is always global to share memories across projects
"""

import json
import shutil
import sys
from pathlib import Path

import click

from .config import get_data_dir
from .core_memory import load_core_memory, core_memory_exists
from .viz import visualize


# Hooks configuration
HOOKS_CONFIG = {
    "hooks": {
        "SessionStart": [
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
def setup():
    """Set up Oubli for Claude Code.

    Installs configuration locally in the current project:
    - .mcp.json (MCP server registration)
    - .claude/settings.local.json (hooks)
    - .claude/commands/ (slash commands)
    - .claude/CLAUDE.md (instructions)

    Data is stored globally in ~/.oubli/ to share memories across all projects.
    """
    project_dir = Path.cwd()
    data_path = get_package_data_path()
    claude_dir = project_dir / ".claude"
    oubli_dir = get_data_dir()  # Always ~/.oubli/

    version = get_version()
    click.echo(f"Setting up Oubli v{version} - Fractal Memory System for Claude Code")
    click.echo("=" * 60)

    # 1. Register MCP server via .mcp.json
    click.echo("\n1. Registering MCP server...")
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
        click.echo(f"   CLAUDE.md installed to .claude/")
    else:
        click.echo("   Warning: CLAUDE.md not found in package data")

    # 5. Create global data directory
    click.echo("\n5. Creating data directory...")
    oubli_dir.mkdir(exist_ok=True)
    click.echo(f"   Data directory: {oubli_dir} (shared across all projects)")

    # 6. Verify data directory and show stats
    click.echo("\n6. Verifying installation...")
    try:
        from .storage import MemoryStore
        store = MemoryStore()
        stats = store.get_stats()
        if stats.total > 0:
            click.echo(f"   ✓ Found {stats.total} memories in {oubli_dir}")
            click.echo(f"   ✓ Core memory: {'exists' if core_memory_exists() else 'not created yet'}")
        else:
            click.echo(f"   ✓ Data directory ready (no memories yet)")
    except Exception as e:
        click.echo(f"   ⚠ Warning: Could not verify data directory: {e}")

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("Setup complete!")
    click.echo("\nWhat was installed:")
    click.echo("  - MCP server: .mcp.json")
    click.echo("  - Hooks: SessionStart, PreCompact, Stop")
    click.echo("  - Slash commands: /clear-memories, /synthesize, /visualize-memory")
    click.echo(f"  - Instructions: .claude/CLAUDE.md")
    click.echo(f"  - Data directory: {oubli_dir} (global, shared)")
    click.echo("\n⚠ IMPORTANT: Restart Claude Code to load the new MCP server.")


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
        click.echo("Hooks merged into .claude/settings.local.json")
    else:
        with open(local_settings_path, "w") as f:
            json.dump(HOOKS_CONFIG, f, indent=2)
        click.echo("Hooks configured in .claude/settings.local.json")

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
    for hook_name in ["SessionStart", "PreCompact", "Stop"]:
        if hook_name in settings["hooks"]:
            del settings["hooks"][hook_name]
            hooks_removed.append(hook_name)

    if hooks_removed:
        with open(local_settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        click.echo(f"Removed hooks: {', '.join(hooks_removed)}")
    else:
        click.echo("No Oubli hooks found to remove")

    click.echo("\nOubli disabled for this project!")


@main.command()
def uninstall():
    """Remove Oubli from the current project.

    Removes:
    - .mcp.json (removes oubli entry)
    - .claude/settings.local.json (removes hooks)
    - .claude/commands/ (removes slash commands)
    - .claude/CLAUDE.md

    Note: Data (~/.oubli/) is NOT deleted to preserve your memories.
    """
    project_dir = Path.cwd()
    claude_dir = project_dir / ".claude"
    oubli_dir = get_data_dir()

    click.echo("Uninstalling Oubli from current project")
    click.echo("=" * 40)

    # 1. Remove MCP server from .mcp.json
    click.echo("\n1. Removing MCP server...")
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
    settings_path = claude_dir / "settings.local.json"

    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)

        if "hooks" in settings:
            hooks_removed = []
            for hook_name in ["SessionStart", "PreCompact", "Stop"]:
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
        click.echo("   No settings.local.json found")

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


@main.command()
def doctor():
    """Diagnose Oubli installation and show debugging info.

    Checks:
    - Installed package version
    - Data directory and memory count
    - Core memory status
    - Project configuration (.mcp.json, hooks)

    Use this to debug issues with memories not appearing.
    """
    project_dir = Path.cwd()
    oubli_dir = get_data_dir()

    click.echo("Oubli Doctor - Diagnostic Report")
    click.echo("=" * 60)

    # 1. Package version
    click.echo("\n1. Package Version")
    version = get_version()
    click.echo(f"   Installed: oubli {version}")

    # Check PyPI version
    try:
        import subprocess
        result = subprocess.run(
            ["pip", "index", "versions", "oubli"],
            capture_output=True, text=True, timeout=10
        )
        if "LATEST:" in result.stdout:
            latest = result.stdout.split("LATEST:")[1].strip().split()[0]
            if latest != version:
                click.echo(f"   ⚠ Newer version available: {latest}")
                click.echo("     Run: pip install --upgrade oubli")
            else:
                click.echo(f"   ✓ Up to date")
    except Exception:
        pass  # Skip PyPI check if it fails

    # 2. Data directory
    click.echo("\n2. Data Directory")
    click.echo(f"   Location: {oubli_dir}")
    if oubli_dir.exists():
        click.echo("   ✓ Directory exists")
        try:
            from .storage import MemoryStore
            store = MemoryStore()
            stats = store.get_stats()
            click.echo(f"   ✓ Memories: {stats.total} total")
            if stats.by_level:
                levels = ", ".join(f"L{k}:{v}" for k, v in sorted(stats.by_level.items()))
                click.echo(f"     By level: {levels}")
        except Exception as e:
            click.echo(f"   ⚠ Could not read memories: {e}")
    else:
        click.echo("   ⚠ Directory does not exist")
        click.echo("     Run: oubli setup")

    # 3. Core memory
    click.echo("\n3. Core Memory")
    core_memory_path = oubli_dir / "core_memory.md"
    if core_memory_exists():
        content = load_core_memory()
        lines = len(content.split("\n")) if content else 0
        chars = len(content) if content else 0
        click.echo(f"   ✓ Exists: {core_memory_path}")
        click.echo(f"   ✓ Size: {lines} lines, {chars} chars")
    else:
        click.echo(f"   - Not created yet")

    # 4. Project configuration
    click.echo("\n4. Project Configuration")
    click.echo(f"   Project: {project_dir}")

    # Check .mcp.json
    mcp_path = project_dir / ".mcp.json"
    if mcp_path.exists():
        with open(mcp_path) as f:
            config = json.load(f)
        if "mcpServers" in config and "oubli" in config["mcpServers"]:
            click.echo("   ✓ MCP server registered in .mcp.json")
        else:
            click.echo("   ⚠ Oubli not in .mcp.json - run: oubli setup")
    else:
        click.echo("   ⚠ No .mcp.json found - run: oubli setup")

    # Check hooks
    settings_path = project_dir / ".claude" / "settings.local.json"
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
        hooks = settings.get("hooks", {})
        oubli_hooks = ["SessionStart", "PreCompact", "Stop"]
        found = [h for h in oubli_hooks if h in hooks]
        if len(found) == 3:
            click.echo("   ✓ All hooks configured")
        elif found:
            click.echo(f"   ⚠ Partial hooks: {', '.join(found)}")
        else:
            click.echo("   ⚠ No hooks configured - run: oubli setup")
    else:
        click.echo("   ⚠ No settings.local.json - run: oubli setup")

    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("If memories aren't appearing in Claude Code:")
    click.echo("  1. Restart Claude Code (MCP servers are cached at session start)")
    click.echo("  2. Run 'oubli setup' to ensure configuration is current")
    click.echo("  3. Check that 'pip show oubli' shows the expected version")


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
            "hookEventName": "SessionStart",
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


@main.command()
@click.option("--speed", "-s", type=float, default=0.008,
              help="Animation speed (delay between columns in seconds)")
@click.option("--static", is_flag=True, default=False,
              help="Print logo without animation")
@click.option("--no-interactive", is_flag=True, default=False,
              help="Disable interactive mode (no mouse clicks, auto-exit)")
def logo(speed, static, no_interactive):
    """Display animated Oubli logo.

    Shows a blocky pixel-art style logo with left-to-right sweep animation.
    In interactive mode (default), click to explode pixels and press Q to quit.
    """
    from .logo import animate_logo, animate_logo_interactive, print_logo_static

    if static:
        print_logo_static()
    elif no_interactive:
        animate_logo(speed=speed)
    else:
        animate_logo_interactive(speed=speed)


@main.command()
@click.option("--demo", is_flag=True, default=False,
              help="Use demo data instead of real memories (for marketing)")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output path for HTML file (default: ~/.oubli/fractal.html)")
@click.option("--no-open", is_flag=True, default=False,
              help="Generate file but don't open in browser")
def fractal(demo, output, no_open):
    """Launch fractal zoom visualization.

    Opens an animated, interactive visualization showing memories as a
    fractal structure. Click to zoom into nodes and reveal their children.

    Features:
    - Auto-play mode for recording demos
    - Hide UI button for clean recordings
    - Smooth GSAP animations with particle effects

    Use --demo for marketing videos with curated sample data.
    """
    import webbrowser

    output_path = Path(output) if output else get_data_dir() / "fractal.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get the fractal viz template
    template_path = get_package_data_path() / "fractal-viz" / "index.html"

    if demo:
        # Just copy the template (it has embedded demo data)
        shutil.copy(template_path, output_path)
        click.echo(f"Fractal visualization (demo mode) saved to: {output_path}")
    else:
        # Load real memories and inject into template
        try:
            from .storage import MemoryStore
            store = MemoryStore()
            memories = store.list(limit=1000)

            if not memories:
                click.echo("No memories found. Use --demo for sample data.")
                click.echo("Or save some memories first using Claude Code.")
                return

            # Convert to JSON format
            memory_data = []
            for m in memories:
                memory_data.append({
                    "id": m.id,
                    "level": m.level,
                    "summary": m.summary,
                    "parent_ids": m.parent_ids or [],
                    "child_ids": m.child_ids or [],
                })

            # Read template and replace demo data
            with open(template_path) as f:
                html = f.read()

            # Find and replace the DEMO_DATA block
            import re
            memories_json = json.dumps(memory_data, indent=12)
            # Replace the memories array in the template
            pattern = r"memories: \[[\s\S]*?\],"
            replacement = f"memories: {memories_json},"
            html = re.sub(pattern, replacement, html, count=1)

            with open(output_path, "w") as f:
                f.write(html)

            click.echo(f"Fractal visualization ({len(memories)} memories) saved to: {output_path}")

        except Exception as e:
            click.echo(f"Error loading memories: {e}")
            click.echo("Use --demo for sample data instead.")
            return

    if not no_open:
        webbrowser.open(f"file://{output_path.absolute()}")


if __name__ == "__main__":
    main()
