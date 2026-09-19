# profile_page

A personal profile page — and, deliberately, a lab.

The page itself is four files of vanilla HTML, CSS and JavaScript with no build step. It is
small on purpose: small enough that every piece of infrastructure around it can be read end to
end and understood completely. That infrastructure is the point of this repository as much as
the page is.

**Live site:** https://emsignailgnehs.github.io/profile_page

## Why the tooling looks oversized

A 108-line page does not need a knowledge base, agent hooks, issue templates and a CI pipeline.
This repository has them because it is where I work through those concepts on something real
rather than on a tutorial. Each one is chosen to teach something specific, and the table below
is the map: concept on the left, the file that implements it on the right.

If you are here to judge the engineering, judge it by whether each piece is understood and
justified, not by its ratio to the product.

## Concept map

| Concept | Where it lives | Status |
|---|---|---|
| Project context for AI sessions | `CLAUDE.md` | done |
| Editor and formatting conventions | `.editorconfig` | done |
| Knowledge base (external sources → cited articles) | `.claude/skills/karpathy-llm-wiki/`, `wiki/`, `raw/` | planned |
| Deterministic agent guardrails (hooks) | `.claude/settings.json` | planned |
| Issue and PR workflow | `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md` | planned |
| Continuous deployment | `.github/workflows/deploy.yml` | planned |
| Quality gates (lint, a11y, links, evidence) | `.github/workflows/` | planned |
| Content as data | `data/projects.json` | planned |

## Running it locally

There is no build step and no dependencies.

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

Opening `index.html` directly in a browser also works today, but will break once content is
loaded over `fetch`, so prefer the server.

## Layout

```
index.html      the page
style.css       all styles
script.js       the contact-info toggle
profile.jpg     avatar
```

## A note on the wiki

`raw/` and `wiki/` (once present) are a knowledge base of external sources — documentation and
articles I read while building this — compiled into cited articles. They are not documentation
of this codebase, and they are excluded from the published site. They share this repository for
convenience, not because they describe the page.

## License

MIT for the code — see [LICENSE](LICENSE). The profile photo and biographical content are not
covered by it.
