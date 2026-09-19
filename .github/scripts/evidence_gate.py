#!/usr/bin/env python3
"""CI gate for the knowledge base's grounding invariant.

Runs the wiki skill's evidence check and decides whether the build fails.

Evidence errors fail the build: they mean an article cannot be verified at all
(no Raw field, an unresolvable link, a link escaping the sources directory).
Fidelity suspects only warn — the checker greps for high-signal literals, so
derived values and product names surface as candidates rather than verdicts,
and a human decides.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".claude" / "skills" / "karpathy-llm-wiki" / "scripts" / "check_evidence.py"
SUMMARY = re.compile(
    r"(\d+) fidelity suspect\(s\), (\d+) evidence error\(s\), (\d+) unreferenced raw file\(s\)"
)


def main() -> int:
    if not (ROOT / "wiki").is_dir():
        print("no knowledge base yet; nothing to verify")
        return 0

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(ROOT)], capture_output=True, text=True
    )
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    match = SUMMARY.search(proc.stdout)
    if not match:
        print("::error::could not parse the evidence report; the checker's output format changed")
        return 1

    suspects, errors, orphans = (int(g) for g in match.groups())
    print(
        f"::notice::{suspects} fidelity suspect(s), {errors} evidence error(s), "
        f"{orphans} unreferenced source file(s)"
    )
    if suspects:
        print("::warning::fidelity suspects need a human to judge them against the source")
    if errors:
        print("::error::articles could not be verified against their sources")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
