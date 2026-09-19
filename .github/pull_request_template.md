## What this changes

<!-- One or two sentences. Link the issue it closes. -->

Closes #

## Why

<!-- The reason, not the mechanics — the diff already shows the mechanics. -->

## Checks

- [ ] `python3 .claude/hooks/tests/test_guard_raw.py` passes
- [ ] Evidence check reports no errors, if this touches the knowledge base
- [ ] Nothing under `raw/` was modified — sources are immutable once collected
- [ ] `README.md`'s concept map is still accurate, if this adds or completes a concept

## If this adds infrastructure

- [ ] It teaches something specific, and the issue says what
- [ ] Anything needing judgement went into a skill or `CLAUDE.md`, not a hook
- [ ] Any new gate was watched to fail before being trusted to pass
