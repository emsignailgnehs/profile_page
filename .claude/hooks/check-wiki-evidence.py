#!/usr/bin/env python3
"""Stop hook: verify the wiki's grounding invariant before the turn ends.

Every load-bearing fact in wiki/ must appear verbatim in a linked raw/ file.
check_evidence.py greps for that; this wrapper runs it and reports findings.

Reporting goes through hookSpecificOutput.additionalContext on stdout, NOT
stderr: stderr from a hook that exits 0 reaches the debug log only, never the
transcript, so a stderr-and-exit-0 hook reports to nobody. additionalContext
is non-error feedback — the conversation continues so the findings can be
acted on, without the transcript showing a hook error. It runs under the same
loop protections as a blocking decision (stop_hook_active and the
8-consecutive-continuation cap); stop_hook_active is honoured below so the
check reports once rather than on every continuation.
"""
import json
import os
import re
import subprocess
import sys

SUMMARY = re.compile(
    r"(\d+) fidelity suspect\(s\), (\d+) evidence error\(s\), (\d+) unreferenced raw file\(s\)"
)
CAP = 9000  # additionalContext is capped at 10,000 characters


def emit(text: str) -> int:
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": text[:CAP]}},
        sys.stdout,
    )
    return 0


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        event = {}

    # Already continuing because of a Stop hook: don't report again.
    if event.get("stop_hook_active"):
        return 0

    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    if not os.path.isdir(os.path.join(root, "wiki")):
        return 0

    script = os.path.join(
        root, ".claude", "skills", "karpathy-llm-wiki", "scripts", "check_evidence.py"
    )
    if not os.path.isfile(script):
        return 0

    try:
        proc = subprocess.run(
            [sys.executable, script, root], capture_output=True, text=True, timeout=120
        )
    except (OSError, subprocess.SubprocessError):
        return 0

    match = SUMMARY.search(proc.stdout)
    if not match:
        return 0

    suspects, errors, orphans = (int(g) for g in match.groups())
    if suspects == 0 and errors == 0:
        return 0

    return emit(
        "Wiki evidence check found problems — a claim in wiki/ could not be located in its "
        f"linked raw/ source ({suspects} fidelity suspect(s), {errors} evidence error(s), "
        f"{orphans} unreferenced raw file(s)). Suspects are candidates, not verdicts: judge "
        "each against the raw context and correct only real mismatches.\n\n" + proc.stdout
    )


if __name__ == "__main__":
    sys.exit(main())
