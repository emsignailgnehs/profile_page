# Claude Code Hooks

> Sources: Anthropic, Claude Code documentation
> Raw: [Hooks reference](../../raw/claude-code/hooks-reference.md)
> Updated: 2026-09-19

## Overview

Hooks are handlers that Claude Code runs automatically at points in its lifecycle. They are the
mechanism for behaviour that must happen regardless of what the model decides — the distinction
that matters when choosing between a hook and a skill. A hook fires whenever its event fires and
its matcher matches; an instruction in a prompt is only likely to be followed.

## Lifecycle and cadences

Events fall into three cadences:

- per session: `SessionStart` and `SessionEnd`
- per turn: `UserPromptSubmit`, `Stop`, and `StopFailure`
- on every tool call inside the agentic loop: `PreToolUse` and `PostToolUse`

Command hooks receive JSON context on stdin; HTTP hooks receive the same JSON as the POST request
body. A handler inspects the input, acts, and optionally returns a decision.

## Exit codes

Exit 0 means success and is the intended exit code when printing JSON for structured control.
Exit 2 signals "stop, don't do this" — but what that achieves depends entirely on the event,
because some events represent actions that can still be prevented and others describe things
that already happened.

| Event | Can block on exit 2? | Effect |
|---|---|---|
| `PreToolUse` | Yes | Blocks the tool call |
| `Stop` | Yes | Prevents Claude from stopping, continues the conversation |
| `UserPromptSubmit` | Yes | Blocks prompt processing and erases the prompt |
| `PostToolUse` | No | Shows stderr to Claude; the tool already ran |
| `SessionStart` | No | Shows stderr to user only |
| `SessionEnd` | No | Shows stderr to user only |

## The stderr trap

The single most consequential detail for anyone writing a reporting hook:

> Stderr from a hook that exits 0 goes to the debug log only, never the transcript, and Claude
> never sees it.

So a hook that gathers findings, prints them to stderr and exits 0 to stay "non-blocking" reports
to nobody. The fix is not necessarily to exit 2 — structured JSON output on stdout is usually the
right answer, and it is per-event which fields are honoured.

## How stdout is interpreted

Whether stdout is read as JSON or plain text depends on how it begins and ends, ignoring
surrounding whitespace. Output that starts with `{` and ends with `}` is parsed as JSON; output
starting with anything else is treated as plain text, a JSON array or quoted JSON string included.

For most events stdout goes to the debug log rather than the transcript. The exceptions, where
plain-text stdout is added as context Claude can see and act on, are `UserPromptSubmit`,
`UserPromptExpansion`, `SessionStart`, and `PostModelSwitch`.

A hook's `additionalContext`, `systemMessage`, and `initialUserMessage` strings, and its plain
stdout, are capped at 10,000 characters.

## Reporting from a Stop hook without erroring

`Stop` honours two distinct ways to keep the conversation going:

- `decision: "block"` with a required `reason` — prevents stopping; the transcript shows a hook
  error.
- `hookSpecificOutput.additionalContext` — "Non-error feedback for Claude. The conversation
  continues so Claude can act on it". Unlike a blocking decision it is shown in the transcript as
  hook feedback rather than a hook error.

The second is what a linting or verification hook wants: it reports findings, Claude can act on
them, and nothing is labelled an error. Both run through the same loop protections — the
`stop_hook_active` input and the 8-consecutive-continuation cap.

A hook that blocks by exiting 2 routes the same way as `reason`: Claude receives the stderr
message as the explanation for why it should continue.

## Applied in this repository

`.claude/settings.json` registers three hooks, each taking a job that needs no judgement:
`SessionStart` loads the wiki index, `PreToolUse` refuses writes under `raw/`, and `Stop` runs the
knowledge base's evidence check. Updating the wiki deliberately stays out of the hooks, because
triage between New, Update, Disputed and No material is judgement and belongs to the skill.

Ingesting this reference corrected two mistakes in that first implementation:

- The `Stop` hook reported findings on stderr and exited 0, which per the stderr rule above meant
  nothing was reported at all. It now returns `hookSpecificOutput.additionalContext` on stdout and
  honours `stop_hook_active` so it speaks once rather than on every continuation.
- The `PreToolUse` matcher covered only `Write|Edit`, so a shell redirect wrote to `raw/`
  unimpeded. The matcher now includes `Bash` and the handler inspects the command string. That
  part is a heuristic rather than a boundary: it catches redirection and the common mutating
  commands while allowing reads, and git remains the real recovery path.
