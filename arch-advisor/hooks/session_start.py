#!/usr/bin/env python3
"""
Arch Advisor — SessionStart Hook

Loads the current arch-advisor session context at the start of each conversation,
allowing the user to resume an in-progress architecture design session.
"""

import json
import os
import sys
from pathlib import Path


def load_session() -> dict | None:
    """Read the current arch session file if it exists."""
    # Try current working directory first, then home directory
    candidates = [
        Path(os.getcwd()) / ".claude" / "arch-session.md",
        Path.home() / ".claude" / "arch-session.md",
    ]
    for path in candidates:
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            if content:
                return {"path": str(path), "content": content}
    return None


def main():
    session = load_session()
    if session is None:
        # No session — nothing to inject
        sys.exit(0)

    # Check if there is an active (non-complete) session
    if "Status: complete" in session["content"]:
        # Session is finished — don't clutter context
        sys.exit(0)

    # Extract title and status for the summary line
    title_line = next(
        (line for line in session["content"].splitlines() if line.startswith("## Session:")),
        "## Session: (untitled)",
    )
    status_line = next(
        (line for line in session["content"].splitlines() if line.startswith("Status:")),
        "Status: unknown",
    )

    # Inject a brief context note into the conversation
    context = {
        "type": "info",
        "message": (
            f"[Arch Advisor] Active architecture session detected.\n"
            f"{title_line}\n"
            f"{status_line}\n\n"
            f"Run `/arch-advisor` to resume, or `/arch-advisor new` to start fresh."
        ),
    }
    print(json.dumps(context))
    sys.exit(0)


if __name__ == "__main__":
    main()
