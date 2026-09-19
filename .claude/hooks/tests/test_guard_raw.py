#!/usr/bin/env python3
"""Tests for the raw/ guard hook.

Run: python3 .claude/hooks/tests/test_guard_raw.py

The guarded directory name is assembled at runtime rather than written as a
literal, so that running these tests is not itself mistaken for an attempt to
write under it.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GUARD = os.path.join(ROOT, ".claude", "hooks", "guard-raw.py")
R = "r" + "aw"

BLOCK = [
    ("bash: append redirect", "Bash", {"command": f"echo x >> {R}/topic/a.md"}),
    ("bash: truncate redirect", "Bash", {"command": f"echo x > ./{R}/a.md"}),
    ("bash: sed -i", "Bash", {"command": f"sed -i s/a/b/ {R}/a.md"}),
    ("bash: rm -rf dir", "Bash", {"command": f"rm -rf {R}"}),
    ("bash: rm file", "Bash", {"command": f"rm {R}/a.md"}),
    ("bash: tee", "Bash", {"command": f"cat foo | tee {R}/a.md"}),
    ("bash: cp into", "Bash", {"command": f"cp /tmp/x.md {R}/"}),
    ("bash: mv into", "Bash", {"command": f"mv /tmp/x.md {R}/a.md"}),
    ("write: relative path", "Write", {"file_path": f"{R}/topic/a.md"}),
    ("edit: absolute path", "Edit", {"file_path": os.path.join(ROOT, R, "a.md")}),
    # Stripping heredoc bodies must not blind the guard to a real redirect,
    # which sits on the command line ahead of the body.
    (
        "bash: heredoc actually writing into the guarded dir",
        "Bash",
        {"command": f"cat > {R}/topic/a.md <<'EOF'\nsome content\nEOF"},
    ),
]

ALLOW = [
    ("bash: cat is a read", "Bash", {"command": f"cat {R}/topic/a.md"}),
    ("bash: grep is a read", "Bash", {"command": f"grep -n x {R}/a.md"}),
    ("bash: cp out of guarded dir", "Bash", {"command": f"cp {R}/a.md /tmp/backup.md"}),
    ("bash: write to wiki", "Bash", {"command": "echo x > wiki/a.md"}),
    ("bash: prefix collision", "Bash", {"command": f"echo x > {R}hide/a.md"}),
    ("bash: git add", "Bash", {"command": f"git add {R}/"}),
    ("write: wiki article", "Write", {"file_path": "wiki/topic/a.md"}),
    ("edit: site file", "Edit", {"file_path": "index.html"}),
    ("edit: prefix collision", "Edit", {"file_path": f"{R}hide/a.md"}),
    # A heredoc body is data. A commit message may quote a redirect without
    # performing one, and blocking that would make the guard unusable.
    (
        "bash: redirect quoted inside a heredoc",
        "Bash",
        {"command": f"git commit -F - <<'MSG'\nfixed: `echo x >> {R}/file` slipped past\nMSG"},
    ),
    (
        "bash: heredoc writing a doc that mentions the path",
        "Bash",
        {"command": f"cat > notes.md <<'EOF'\nnever run: rm -rf {R}\nEOF"},
    ),
]


def run(tool, tool_input):
    payload = json.dumps({"cwd": ROOT, "tool_name": tool, "tool_input": tool_input})
    proc = subprocess.run(
        [sys.executable, GUARD], input=payload, capture_output=True, text=True
    )
    return proc.returncode


def main():
    failures = []

    for name, tool, tool_input in BLOCK:
        if run(tool, tool_input) != 2:
            failures.append(f"{name}: expected exit 2, was allowed")

    for name, tool, tool_input in ALLOW:
        if run(tool, tool_input) != 0:
            failures.append(f"{name}: expected exit 0, was blocked")

    # Malformed input must never take the tool call down.
    proc = subprocess.run(
        [sys.executable, GUARD], input="not json", capture_output=True, text=True
    )
    if proc.returncode != 0:
        failures.append("malformed stdin: expected exit 0")

    total = len(BLOCK) + len(ALLOW) + 1
    for failure in failures:
        print(f"FAIL  {failure}")
    print(f"{total - len(failures)}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
