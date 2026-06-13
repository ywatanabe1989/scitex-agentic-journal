"""Local deterministic reviewer adapter — no LLM, no network.

Implements the :class:`ReviewerAdapter` protocol with a hand-rolled,
fully-deterministic payload per sub-report so the M2 pipeline (Gate-1
record → ReviewRunner → persisted review) runs end-to-end *without*
needing API tokens for Qwen / Spartan / Claude. The output is NOT a
real review — it's a structural placeholder that lets downstream
gates exercise their shapes (decision engine #7, persistent ID #8,
publish hand-off #9).

The acceptance language in #6 names this provider explicitly:
"Spartan / Qwen / local". This module is the "local" branch — useful
for development, CI, and the operator's local-staging bring-up
before any live LLM endpoint exists.

Each sub-report is honest about what it can and cannot say without
real model output:

* reproducibility: ``passed=True``, ``sandbox_image='local-deterministic'``
  with a note that no sandbox actually ran.
* claim_verify: empty triage — the runner does not re-run
  ``clew claim verify`` from here; the Gate-1 verdict already
  carries that result.
* novelty: ``overlap_score=0.0`` (i.e. no signal), no neighbours.
* methodology: empty :class:`Criticism` tuple, ``Severity.NONE``.
"""

from __future__ import annotations

from scitex_agentic_journal._review._rubric import SubReportKind
from scitex_agentic_journal._review._types import (
    AdapterMode,
    ClaimVerifyReport,
    MethodologyReport,
    NoveltyReport,
    ReproducibilityReport,
    ReviewSubReport,
    ReviewerAdapter,
    SubmissionInputs,
)


_NOTE = (
    "local-deterministic adapter — no LLM ran. Use only for "
    "structural pipeline development; replace with a live "
    "Qwen/Spartan adapter for an editorial decision."
)


class LocalDeterministicAdapter:
    """Hand-rolled, no-network adapter — satisfies :class:`ReviewerAdapter`.

    Static analogue of the Qwen / Spartan adapters: same shape, same
    method, deterministic output. The output is honest about its
    placeholder nature via the embedded note strings.
    """

    adapter_name: str = "local-deterministic"
    adapter_version: str = "0.1.0"
    mode: AdapterMode = "stub"

    def run_sub_report(
        self,
        kind: SubReportKind,
        inputs: SubmissionInputs,
        prompts_version: str,
    ) -> ReviewSubReport:
        del prompts_version  # version is captured in ReviewRecord
        if kind is SubReportKind.REPRODUCIBILITY:
            return ReviewSubReport(
                kind=kind,
                payload=ReproducibilityReport(
                    passed=True,
                    sandbox_image="local-deterministic",
                    notes=_NOTE,
                ),
            )
        if kind is SubReportKind.CLAIM_VERIFY:
            return ReviewSubReport(
                kind=kind,
                payload=ClaimVerifyReport(
                    green_claim_ids=(),
                    yellow_claim_ids=(),
                    red_claim_ids=(),
                ),
            )
        if kind is SubReportKind.NOVELTY:
            return ReviewSubReport(
                kind=kind,
                payload=NoveltyReport(
                    overlap_score=0.0,
                    nearest_neighbour_dois=(),
                ),
            )
        if kind is SubReportKind.METHODOLOGY:
            return ReviewSubReport(
                kind=kind,
                payload=MethodologyReport(criticisms=()),
            )
        # Defensive — the SubReportKind enum is closed so we should
        # never get here; raise loudly if we do.
        raise ValueError(
            f"LocalDeterministicAdapter does not know how to run sub-report "
            f"kind {kind!r}; this is a bug in scitex-agentic-journal."
        )


# Static structural check at import time — protects against a future
# refactor that breaks the protocol shape.
_check: ReviewerAdapter = LocalDeterministicAdapter()
del _check
