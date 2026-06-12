# Changelog

All notable changes to `scitex-agentic-journal` are documented in this file.

## [Unreleased]

### Added
- `scitex_agentic_journal._gate1` package — first slice of the M1 submission
  gate. Public surface: `GateFailure` (structured failure exception),
  `verify_orcid(orcid_id, *, session=None, base_url=...)`, `OrcidRecord`,
  and `ORCID_PUB_API_BASE` constant.
- `verify_orcid` resolves an ORCID iD against the public ORCID v3.0 API
  via real HTTP (`requests`). Accepts bare iDs and any `orcid.org` /
  `sandbox.orcid.org` URL form. Verifies the ISO 7064 MOD 11-2 check
  digit before any network call. Loud, structured `GateFailure` on
  malformed iD / bad checksum / 404 / non-2xx / non-JSON body /
  unfamiliar record shape / network unreachable. No silent fallbacks,
  no mocks.
- `tests/test_gate1_orcid.py` — hermetic test suite that spins up a real
  local stdlib `http.server` on an ephemeral port and exercises
  `verify_orcid` over real TCP via the `base_url` config seam (no
  monkey-patching, no respx/responses replay library — STX-NM001-003 /
  PA-306 compliant). One opt-in `@pytest.mark.network` test hits the
  real `pub.orcid.org` when `SCITEX_RUN_NETWORK_TESTS=1`.
- `pyproject.toml`: register the `network` pytest marker.
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
