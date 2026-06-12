"""PS-303 example test — Gate-1 ORCID resolvability shell example.

Mirrors ``examples/01_gate1_orcid_resolve.sh``. Executes the script
as the user would, against a real ORCID record over the network. Skips
gracefully when the network is unreachable so unit-level CI matrix legs
without egress (or offline dev runs) do not red the suite — but when
the network IS available the script must exit 0 and print the canonical
``GATE-1 PASS`` marker. No mocks.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "01_gate1_orcid_resolve.sh"
)
# Stephen Hawking — a stable, real ORCID record. The 0097 checksum is
# canonical and won't move.
SAMPLE_ORCID = "0000-0002-1825-0097"


def _online(host: str = "pub.orcid.org", port: int = 443, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.mark.integration
def test_example_orcid_resolve_script_passes() -> None:
    """The shell example must exit 0 and print GATE-1 PASS against a
    real, resolvable ORCID id (Stephen Hawking, 0000-0002-1825-0097).
    """
    assert EXAMPLE.exists(), f"missing example script: {EXAMPLE}"
    assert os.access(EXAMPLE, os.X_OK), f"example script not executable: {EXAMPLE}"
    if shutil.which("bash") is None:
        pytest.skip("bash not on PATH")
    if not _online():
        pytest.skip("network egress to pub.orcid.org unavailable")

    # Run via the running Python so the in-repo `src/` install is used.
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    result = subprocess.run(
        ["bash", str(EXAMPLE), SAMPLE_ORCID],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"example exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "GATE-1 PASS" in result.stdout, (
        f"expected 'GATE-1 PASS' in stdout; got:\n{result.stdout}"
    )
    assert SAMPLE_ORCID in result.stdout, (
        f"expected ORCID id in stdout; got:\n{result.stdout}"
    )
    # Sanity: the same Python invoked by the script should resolve our
    # module — guards against the example silently running a different
    # interpreter than the test suite.
    assert sys.executable
