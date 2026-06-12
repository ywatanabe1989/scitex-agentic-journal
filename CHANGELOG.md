# Changelog

All notable changes to `scitex-agentic-journal` are documented in this file.

## [Unreleased]

### Added
- README "What it is" section spelling out the AI-agent-driven peer-review /
  copy-edit / publication-readiness role, and an explicit "MVP loop"
  (submit → agent review → decision → publish) section that maps to the
  initial GitHub issues.
- README "Full pipeline (design target)" section with a 4-gate flow
  (structural gate → AI review → editorial decision → persistent ID) so the
  MVP loop and the long-term target are no longer collapsed.
- Roadmap expanded from 5 to 7 milestones (M1–M7) with an explicit editorial
  decision engine (M3), persistent ID stage (M4), Live Paper hand-off (M5),
  reviewer dashboard (M6) and MCP server (M7).
- `scitex-scholar` added to the dependency direction diagram as the source of
  novelty / literature triangulation.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) running `pytest` on
  Python 3.10 / 3.11 / 3.12 for `push` and `pull_request` against `main` and
  `develop`.
- `pyproject.toml`: `license-files`, extra keywords (`agentic-review`,
  `peer-review`, `reproducibility`), extra classifiers
  (`Framework :: Django`, information analysis, LaTeX), and a `Changelog`
  project URL.

## [0.1.0-alpha] — 2026-06-12

### Added
- Initial scaffold with purpose + 5-milestone roadmap.
- README pipeline diagram (submit -> ORCID+code+DAG gate -> AI review -> persistent ID -> Live Paper).
- Dependency direction documented: consumer of `scitex-clew` (claim model owner), emits to `scitex-live-paper`.
- `pyproject.toml` with `scitex-dev`, `scitex-ui`, `django`, `click`, `requests`, `pyyaml` runtime deps.
- Package skeleton at `src/scitex_agentic_journal/` with version export.
- Smoke test.
