#!/usr/bin/env python3
"""PreToolUse hook: refuse writes under raw/.

The wiki skill declares raw/ immutable, which is what makes its grounding
invariant meaningful: a fact verified against a raw file stays verified only
if that file cannot change afterwards. An instruction asking the agent not to
edit raw/ is merely likely to be followed; this is not.

Exit 2 denies the tool call and stderr becomes the reason the agent sees.

Covers Write and Edit exactly, by resolving the target path. Bash coverage is
necessarily a heuristic over the command string — it catches redirection into
raw/ and the common mutating commands, and deliberately allows reads such as
`cat raw/x` or `cp raw/x /tmp/`. It is defence in depth, not a security
boundary: a determined script can still get through, and nothing here is a
substitute for raw/ being restorable from git.
"""
import json
import os
import re
import sys

GUARD = "raw"

# Redirection into raw/:  > raw/x   >> ./raw/x   >"raw/x"
REDIRECT = re.compile(r">>?\s*['\"]?(?:\./)?raw/")
# Commands that mutate whatever path follows them.
IN_PLACE = re.compile(
    r"\b(?:sed\s+-[a-zA-Z]*i|perl\s+-[a-zA-Z]*i|tee(?:\s+-[a-zA-Z]+)*|truncate|shred|dd)\b"
    r"[^|;&]*?(?:\./)?raw/"
)
# Destructive commands naming raw/ anywhere in their arguments.
DESTRUCTIVE = re.compile(r"\brm\b[^|;&]*?(?:\./)?raw(?:/|\b)")
# mv/cp/install write to their LAST argument.
MOVE_COPY = re.compile(r"\b(?:mv|cp|install|rsync)\b([^|;&]*)")
# Heredoc bodies are data, not commands: a commit message or a file being
# written can quote a shell redirect without performing one.
HEREDOC = re.compile(
    r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?\s*?\n.*?^\s*\1\s*$",
    re.DOTALL | re.MULTILINE,
)


def strip_heredocs(command: str) -> str:
    return HEREDOC.sub("\n", command)


def bash_writes_to_raw(command: str) -> bool:
    command = strip_heredocs(command)
    if REDIRECT.search(command) or IN_PLACE.search(command) or DESTRUCTIVE.search(command):
        return True
    for match in MOVE_COPY.finditer(command):
        args = [a for a in match.group(1).split() if not a.startswith("-")]
        if args and re.match(r"^['\"]?(?:\./)?raw(?:/|['\"]?$)", args[-1]):
            return True
    return False


def path_under_raw(path: str, root: str) -> bool:
    target = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
    guarded = os.path.join(os.path.realpath(root), GUARD)
    return target == guarded or target.startswith(guarded + os.sep)


def deny(what: str) -> int:
    print(
        f"Blocked: {what} would write under raw/, which is immutable source material.\n"
        "The wiki's grounding invariant depends on raw files never changing after they are "
        "collected. To correct a source, collect it again under a new filename; to change "
        "what the wiki says about it, edit the article in wiki/.",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool = event.get("tool_name") or ""
    tool_input = event.get("tool_input") or {}
    root = event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    if tool == "Bash":
        command = tool_input.get("command") or ""
        return deny("this command") if bash_writes_to_raw(command) else 0

    path = tool_input.get("file_path") or tool_input.get("path") or ""
    if path and path_under_raw(path, root):
        return deny(os.path.relpath(os.path.realpath(
            path if os.path.isabs(path) else os.path.join(root, path)), os.path.realpath(root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
