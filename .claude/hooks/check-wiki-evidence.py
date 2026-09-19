#!/usr/bin/env python3
"""Stop hook: verify the wiki's grounding invariant before the turn ends.

Every load-bearing fact in wiki/ must appear verbatim in a linked raw/ file.
check_evidence.py greps for that; this wrapper runs it and surfaces findings.

Reports without blocking (exit 0). The linter flags suspects, not certainties,
and a Stop hook that blocks on a false positive traps the turn. Switch the
marked return to 2 once you trust its output on your own wiki.
"""
import os
import re
import subprocess
import sys

SUMMARY = re.compile(
    r"(\d+) fidelity suspect\(s\), (\d+) evidence error\(s\), (\d+) unreferenced raw file\(s\)"
)


def main() -> int:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isdir(os.path.join(root, "wiki")):
        return 0

    script = os.path.join(
        root, ".claude", "skills", "karpathy-llm-wiki", "scripts", "check_evidence.py"
    )
    if not os.path.isfile(script):
        return 0

    try:
        proc = subprocess.run(
            [sys.executable, script, root],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"evidence check could not run: {exc}", file=sys.stderr)
        return 0

    match = SUMMARY.search(proc.stdout)
    if not match:
        return 0

    suspects, errors, orphans = (int(g) for g in match.groups())
    if suspects == 0 and errors == 0:
        return 0

    print(
        "Wiki evidence check found problems — a claim in wiki/ could not be located "
        f"in its linked raw/ source ({suspects} fidelity suspect(s), {errors} evidence "
        f"error(s), {orphans} unreferenced raw file(s)):\n",
        file=sys.stderr,
    )
    print(proc.stdout, file=sys.stderr)
    return 0  # change to 2 to make this blocking


if __name__ == "__main__":
    sys.exit(main())
