#!/usr/bin/env python3
"""PreToolUse hook: refuse writes under raw/.

The wiki skill declares raw/ immutable, which makes its grounding invariant
meaningful: a fact verified against a raw file stays verified. An instruction
asking the agent not to edit raw/ is merely likely to be followed; this is not.

Exit 2 denies the tool call and stderr becomes the reason the agent sees.
"""
import json
import os
import sys


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not path:
        return 0

    root = os.path.realpath(event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    target = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
    guarded = os.path.join(root, "raw")

    if target == guarded or target.startswith(guarded + os.sep):
        rel = os.path.relpath(target, root)
        print(
            f"Blocked: {rel} is under raw/, which is immutable source material.\n"
            "The wiki's grounding invariant depends on raw files never changing after "
            "they are collected. To correct a source, collect it again under a new "
            "filename; to change what the wiki says about it, edit the article in wiki/.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
