#!/usr/bin/env python3
"""SessionStart hook: put the knowledge-base index in front of the agent.

Deterministic context loading — no judgement involved, so a hook is the right
mechanism. Silent no-op until the wiki exists.
"""
import json
import os
import sys

LIMIT = 4000


def main() -> int:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    index = os.path.join(root, "wiki", "index.md")
    if not os.path.isfile(index):
        return 0

    try:
        with open(index, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return 0

    if not text.strip():
        return 0
    if len(text) > LIMIT:
        text = text[:LIMIT] + "\n\n[...truncated; read wiki/index.md for the rest]"

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    "Knowledge base index (wiki/index.md). These are compiled articles "
                    "about external sources, not documentation of this codebase:\n\n" + text
                ),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
