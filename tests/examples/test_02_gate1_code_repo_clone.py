"""PS-303 example test — Gate-1 code-repo cloneability shell example.

Mirrors ``examples/02_gate1_code_repo_clone.sh``. Executes the script
as the user would, performing a real shallow ``git clone`` of a small
public repo. Skips gracefully when ``git`` is missing or the network is
unreachable — but when both are present the script must exit 0 and
print the canonical ``GATE-1 PASS`` marker plus a head commit. No
mocks.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

EXAMPLE = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "02_gate1_code_repo_clone.sh"
)
# GitHub's canonical tutorial repo. Tiny (a single README), public, and
# stable since 2011 — chosen so the clone runs in <2 s even on slow
# links and we don't pay the bandwidth of a real research repo.
SAMPLE_REPO = "https://github.com/octocat/Hello-World.git"


def _online(host: str = "github.com", port: int = 443, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.mark.integration
def test_example_code_repo_clone_script_passes() -> None:
    """The shell example must exit 0 and print GATE-1 PASS against a
    real, public git repo (octocat/Hello-World).
    """
    assert EXAMPLE.exists(), f"missing example script: {EXAMPLE}"
    assert os.access(EXAMPLE, os.X_OK), f"example script not executable: {EXAMPLE}"
    if shutil.which("bash") is None:
        pytest.skip("bash not on PATH")
    if shutil.which("git") is None:
        pytest.skip("git not on PATH")
    if not _online():
        pytest.skip("network egress to github.com unavailable")

    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    result = subprocess.run(
        ["bash", str(EXAMPLE), SAMPLE_REPO],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"example exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "GATE-1 PASS" in result.stdout, (
        f"expected 'GATE-1 PASS' in stdout; got:\n{result.stdout}"
    )
    assert "HEAD commit" in result.stdout, (
        f"expected 'HEAD commit' in stdout; got:\n{result.stdout}"
    )
    assert SAMPLE_REPO in result.stdout, (
        f"expected repo URL in stdout; got:\n{result.stdout}"
    )
