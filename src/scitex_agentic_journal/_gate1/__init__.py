"""Gate-1: structural submission checks (ORCID, code repo, Clew DAG).

Gate-1 is the no-AI gate. It is a fast, deterministic, network-only check
that the submission bundle is well-formed and the author can be reached.

Public surface — only what we need today:

- :class:`GateFailure` — structured failure raised by any gate-1 check.
- :func:`verify_orcid` — resolve an ORCID iD against the public ORCID API.

The orchestrating CLI (``scitex-agentic-journal submit``) wires these
checks together; that wiring is tracked separately under issue #5 (M1 CLI).
"""

from scitex_agentic_journal._gate1._errors import GateFailure
from scitex_agentic_journal._gate1._orcid import (
    ORCID_PUB_API_BASE,
    OrcidRecord,
    verify_orcid,
)

__all__ = [
    "GateFailure",
    "ORCID_PUB_API_BASE",
    "OrcidRecord",
    "verify_orcid",
]
