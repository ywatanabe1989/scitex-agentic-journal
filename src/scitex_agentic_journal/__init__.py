"""SciTeX Agentic Journal — ARA-native AI-reviewed open publishing on top of Clew.

Pipeline: submit -> ORCID+code+DAG gate -> AI review (Spartan Qwen) -> internal
persistent ID -> Live Paper.

Status: pre-alpha scaffold. M1 (submission gate) implementation pending.

See README.md for the dependency graph and roadmap.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("scitex-agentic-journal")
except PackageNotFoundError:  # pragma: no cover - source-tree fallback
    # PEP 440 local-segment fallback for in-tree / editable installs that
    # are not yet registered with importlib.metadata. Audit rule PA-203.
    __version__ = "0.0.0+local"


# M4 paper-level re-review badge — agentic-journal → live-paper contract.
# Re-exported at the package top so a hub-side resolver writes
# ``from scitex_agentic_journal import resolve_badge_for_paper`` instead
# of digging into the underscored submodule.
from scitex_agentic_journal._re_review_badge import (
    ReReviewBadge,
    ReReviewStatus,
    resolve_badge_for_paper,
    verdict_to_status,
)

__all__ = [
    "ReReviewBadge",
    "ReReviewStatus",
    "__version__",
    "resolve_badge_for_paper",
    "verdict_to_status",
]
