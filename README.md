<!-- ---
!-- Timestamp: 2026-06-12
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/scitex-agentic-journal/README.md
!-- --- -->

# SciTeX Agentic Journal (`scitex-agentic-journal`)

ARA-native AI-reviewed open publishing on top of [Clew](https://github.com/ywatanabe1989/scitex-clew).

> **Status:** pre-alpha scaffold (v0.1.0-alpha). README + minimum package skeleton. M1 (submission gate) implementation pending.

## What problem does it solve?

Traditional peer review is slow, opaque, volunteer-limited, and cannot keep pace with the preprint flood. Meanwhile AI agents can now read, run, and verify the entire research workflow — code, data, claims, provenance — in minutes. `scitex-agentic-journal` turns that capability into a publication venue.

## Pipeline

```
   submit (manuscript + project repo + Clew DAG)
      |
      v
   gate 1: ORCID + code repo + DAG completeness check
      |
      v
   gate 2: AI review (Spartan / Qwen-class reviewer agents)
      |     - reproducibility re-run + claim verify
      |     - novelty + literature triangulation (Scholar)
      |     - methodology critique
      |
      v
   gate 3: internal persistent ID
      |       (JaLC after incorporation; Zenodo DOI interim;
      |        sandbox-DOI for dev)
      |
      v
   publish -> Live Paper (`scitex-live-paper`)
```

## Dependency direction

```
scitex-agentic-journal   --reads-->   scitex-clew         (claim model + DAG)
scitex-agentic-journal   --emits-->   scitex-live-paper   (rendered artefact)
scitex-agentic-journal   --hosts-on-> scitex-hub          (reviewer dashboard, auth)
```

- The **claim** data model is owned by `scitex-clew` (decision locked in). Agentic-journal is a **consumer** — it does not define new claim types; it reads `VerificationStatus`, the DAG, and the hash-verified provenance graph.
- After acceptance, agentic-journal hands the manuscript bundle (LaTeX + claims + DAG + assets) to `scitex-live-paper` for rendering.
- Hosting (web UI, Auth via Gitea, app surface) is provided by `scitex-hub`. Agentic-journal ships an optional Django app for the reviewer dashboard.

## First milestone (M1, "submission gate")

1. Define `Submission` schema (manuscript bundle + ORCID + code repo URL + clew project path).
2. Implement gate 1 only: structural checks against the submitted bundle — no AI review yet.
   - ORCID resolvable
   - code repo cloneable
   - clew DAG present and `clew claim verify` returns >= 1 green claim
3. CLI: `scitex-agentic-journal submit ./paper/` returns gate-1 verdict (pass / fail + reasons).
4. No mocks. No silent fallbacks. Real errors with guidance.

Subsequent milestones are tracked as separate issues:

- M2 — AI review (Spartan Qwen reviewer agents)
- M3 — persistent ID (sandbox -> Zenodo -> JaLC)
- M4 — publish to `scitex-live-paper`
- M5 — reviewer dashboard on `scitex-hub`

## Install (planned)

```bash
pip install scitex-agentic-journal           # CLI + library
pip install scitex-agentic-journal[mcp]      # + MCP server for agents
pip install scitex-agentic-journal[test]     # + dev/test extras
```

## Part of SciTeX

`scitex-agentic-journal` is part of [SciTeX](https://scitex.ai).

Upstream dependencies:

| Package | Provides | Used here for |
|---------|----------|---------------|
| `scitex-clew`    | claim model + DAG + verification | submission gate, AI review evidence |
| `scitex-scholar` | literature search                | novelty / triangulation in AI review |
| `scitex-writer`  | manuscript bundle format         | submission ingestion |
| `scitex-hub`     | hosting (web UI, Auth, app store)| reviewer dashboard surface |
| `scitex-ui`      | UI shell + components            | reviewer dashboard, future viewer wiring |
| `scitex-dev`     | CLI scaffolds, validate-version  | dev tooling |

Downstream consumer:

| Package | Receives | For |
|---------|----------|-----|
| `scitex-live-paper` | accepted manuscript + claims + DAG | rendered interactive paper |

## Status

Pre-alpha — design + scaffold only. Implementation tracked under issues.

## License

AGPL-3.0-only.

<!-- EOF -->
