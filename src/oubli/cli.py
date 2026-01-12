"""CLI commands for Oubli.

Provides command-line interface for memory operations and session hooks.
"""

import json
import sys
from .core_memory import load_core_memory, core_memory_exists


def inject_context():
    """Output core memory as JSON for UserPromptSubmit hook.

    This command is called on every user prompt to inject
    core memory into the conversation context.
    """
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


def session_start():
    """Output core memory for SessionStart hook (legacy).

    This command is called by the SessionStart hook to inject
    core memory into the conversation context.
    """
    if not core_memory_exists():
        print("No core memory found. Use core_memory_save to create one.")
        return

    content = load_core_memory()
    if content:
        print("# Core Memory (loaded automatically)\n")
        print(content)
    else:
        print("Core memory file exists but is empty.")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m oubli.cli <command>")
        print("Commands: inject-context, session-start")
        sys.exit(1)

    command = sys.argv[1]

    if command == "inject-context":
        inject_context()
        sys.exit(0)
    elif command == "session-start":
        session_start()
        sys.exit(0)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
