#!/usr/bin/env python3
"""
Arch Advisor — SessionStart Hook

Reads the lightweight pointer at .claude/arch-advisor/session.md and injects
a resume prompt if there is an active (non-complete) architecture session.
"""

import json
import os
import sys
from pathlib import Path


def load_pointer(cwd: Path) -> dict | None:
    """Read .claude/arch-advisor/session.md from cwd. Returns parsed fields or None."""
    pointer_path = cwd / ".claude" / "arch-advisor" / "session.md"
    if not pointer_path.exists():
        return None
    content = pointer_path.read_text(encoding="utf-8").strip()
    if not content:
        return None

    fields: dict = {}
    for line in content.splitlines():
        for key in ("path", "title", "status", "date"):
            if line.startswith(f"{key}:"):
                fields[key] = line.split(":", 1)[1].strip()

    return fields if fields else None


def main():
    cwd = Path(os.getcwd())
    pointer = load_pointer(cwd)

    if pointer is None:
        sys.exit(0)

    status = pointer.get("status", "")
    if status == "complete":
        # Session finished — nothing to inject
        sys.exit(0)

    session_path = pointer.get("path", "")
    title = pointer.get("title", "(untitled)")
    date = pointer.get("date", "")

    if not session_path:
        sys.exit(0)

    # Verify the session directory actually exists
    full_session_path = cwd / session_path
    session_file = full_session_path / "session.md"

    if session_file.exists():
        message = (
            f"[Arch Advisor] Active session detected: **{title}**\n"
            f"Status: {status} | Date: {date}\n"
            f"Path: {session_path}/\n\n"
            f"Run `/arch-advisor resume {Path(session_path).name}` to continue, "
            f"or `/arch-advisor new` to start a new session."
        )
    else:
        message = (
            f"[Arch Advisor] Session pointer found for **{title}** (status: {status}), "
            f"but the session directory `{session_path}/` was not found in the current working directory.\n\n"
            f"Run `/arch-advisor new` to start a fresh session, or change to the correct directory and reopen."
        )

    context = {"type": "info", "message": message}
    print(json.dumps(context))
    sys.exit(0)


if __name__ == "__main__":
    main()
