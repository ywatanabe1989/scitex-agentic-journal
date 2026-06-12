"""Gate-2 review engine: ARA rubric + runner + versioned prompts + adapter.

The review engine produces a :class:`ReviewRecord` per submission. The
record carries four typed sub-reports (reproducibility, claim verify,
novelty, methodology) plus the prompt and adapter versions used. The
record is **immutable** once written: rules-version + decision live
in `_decision` (M3), not here.

This module only orchestrates. Actual LLM calls live behind a
:class:`ReviewerAdapter` and are not invoked here in unit tests.
"""

from __future__ import annotations

from scitex_agentic_journal._review._qwen_adapter import QwenAdapterStub
from scitex_agentic_journal._review._rubric import (
    ARA_RUBRIC_VERSION,
    AraRubric,
    Severity,
    SubReportKind,
)
from scitex_agentic_journal._review._runner import ReviewRunner
from scitex_agentic_journal._review._types import (
    ClaimVerifyReport,
    Criticism,
    MethodologyReport,
    NoveltyReport,
    ReproducibilityReport,
    ReviewerAdapter,
    ReviewRecord,
    ReviewSubReport,
    SubmissionInputs,
)

__all__ = [
    "ARA_RUBRIC_VERSION",
    "AraRubric",
    "ClaimVerifyReport",
    "Criticism",
    "MethodologyReport",
    "NoveltyReport",
    "QwenAdapterStub",
    "ReproducibilityReport",
    "ReviewRecord",
    "ReviewRunner",
    "ReviewSubReport",
    "ReviewerAdapter",
    "Severity",
    "SubReportKind",
    "SubmissionInputs",
]
