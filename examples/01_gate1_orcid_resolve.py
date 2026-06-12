"""Resolve an ORCID iD against the real ORCID public API (Gate-1 / M1.1).

Run::

    python examples/01_gate1_orcid_resolve.py 0000-0002-1825-0097

The submission gate's first structural check is *can we reach the
author*. This example exercises the same code path the CLI orchestrator
(issue #5) will call: real HTTP via ``requests``, structured
``GateFailure`` on every error class, no silent fallbacks.
"""

from __future__ import annotations

import sys

from scitex_agentic_journal._gate1 import GateFailure, verify_orcid


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: 01_gate1_orcid_resolve.py <ORCID-iD>")
        return 2
    orcid_id = sys.argv[1]
    try:
        record = verify_orcid(orcid_id)
    except GateFailure as fail:
        print(f"GATE-1 FAIL: {fail}")
        return 1
    print(f"GATE-1 PASS — resolved {record.orcid_id} -> {record.display_name!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
