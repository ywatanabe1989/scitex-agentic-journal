---
name: scitex-agentic-journal
description: |
  [WHAT] `scitex-agentic-journal` is the publication-venue substrate of SciTeX: a journal where AI agents (Spartan/Qwen-class reviewer agents) — not volunteer reviewers — perform peer review, reproducibility re-run, claim verification, novelty triangulation, methodology critique, and editorial decision (accept / revise / reject). The package ingests a manuscript bundle (LaTeX + claims + Clew DAG + code repo + ORCID), runs gate-1 structural checks, gate-2 AI review, gate-3 editorial decision, gate-4 persistent ID, then hands off to scitex-live-paper.
  [WHEN] Use when the user asks to submit, review, accept, reject, revise, mint a DOI for, or publish a manuscript via the SciTeX agentic journal; or mentions ARA-native publishing, gate-1 / gate-2 checks, ORCID validation, Clew DAG submission gate, Live Paper hand-off, reviewer agents, or editorial decision engine.
  [HOW] `pip install scitex-agentic-journal` (CLI + library) or `pip install scitex-agentic-journal[mcp]` (+ MCP server for agents). See the leaf skills for submission bundle shape, gate-1 implementation, review engine, decision rules, and publish hand-off.
tags: [scitex-agentic-journal, ara, peer-review, doi, orcid, clew, live-paper]
primary_interface: cli
interfaces:
  python: 2
  cli: 1
  mcp: 2
  django: 3
  skills: 2
---

# scitex-agentic-journal Skill

> **Status:** pre-alpha (v0.1.0-alpha). Skeleton + gate-1 implementation in progress. Skills documented here describe the **target** surface; leaves note implemented vs. planned.

> **Interfaces:** CLI ⭐ · Python ⭐⭐ · MCP ⭐⭐ · Django ⭐⭐⭐ · Skills ⭐⭐

`scitex-agentic-journal` is the journal substrate of SciTeX. It is **not** a new claim model and **not** a new manuscript format; it consumes Clew's claim/DAG model and emits Live Paper bundles. AI agents do the editorial work that volunteer reviewers traditionally do.

## Install & smoke verify

```bash
pip install scitex-agentic-journal           # CLI + library
pip install scitex-agentic-journal[mcp]      # + MCP server for AI agents
python -c "import scitex_agentic_journal; print(scitex_agentic_journal.__version__)"
```

The umbrella `import scitex.agentic_journal` is **not** wired yet — the
sub-package only exposes the standalone import path during alpha.

## Sub-skills (leaves)

- [01_overview.md](01_overview.md) — what the package is, MVP loop, full pipeline, dependency direction
- [02_submission-bundle.md](02_submission-bundle.md) — manuscript bundle shape (LaTeX + claims + Clew DAG + code repo + ORCID)
- [03_gate1-checks.md](03_gate1-checks.md) — structural checks (ORCID resolvable, code repo cloneable, Clew DAG present + ≥1 green claim)
- [04_review-and-decision.md](04_review-and-decision.md) — gate-2 AI review (reproducibility, claim verify, novelty, methodology) + gate-3 editorial decision (accept / revise / reject)
- [05_publish-handoff.md](05_publish-handoff.md) — gate-4 persistent ID (sandbox → Zenodo → JaLC) + hand-off to scitex-live-paper
- [06_python-api.md](06_python-api.md) — top-level Python surface (`Submission`, `Gate1`, `Review`, `Decision`, `Publish`)
- [07_django-and-hub.md](07_django-and-hub.md) — `_django` reviewer dashboard mounted into scitex-hub via `apps/workspace/agentic_journal_app`
- [08_mcp-and-agents.md](08_mcp-and-agents.md) — `_mcp` server: submit / review / decide / publish tools for AI agents

## When NOT to use this skill

- For Clew claim DAGs themselves — that's `scitex-clew`.
- For paper rendering / interactive Live Paper — that's `scitex-live-paper`.
- For literature search — that's `scitex-scholar` (we **consume** it for novelty triangulation but don't reimplement).
- For the host platform (auth, app store, Gitea) — that's `scitex-hub`.

## Dependency direction (read-only summary)

```
scitex-agentic-journal   --reads-->   scitex-clew         (claim model + DAG)
scitex-agentic-journal   --reads-->   scitex-scholar      (literature triangulation)
scitex-agentic-journal   --emits-->   scitex-live-paper   (rendered artefact)
scitex-agentic-journal   --hosts-on-> scitex-hub          (reviewer dashboard, auth)
```

See [01_overview.md](01_overview.md) for the full pipeline diagram and milestone breakdown.
