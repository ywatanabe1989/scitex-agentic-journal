"""Shallow-clone an author's code repo (Gate-1 / M1.2).

Run::

    python examples/02_gate1_code_repo_clone.py https://github.com/octocat/Hello-World.git

The submission gate's second structural check confirms the author's
code is reachable and cloneable. This example exercises the same
``cloned_code_repo`` context manager that the M1 CLI orchestrator
(#5) will use: real ``git`` binary via ``subprocess``, structured
``GateFailure`` on every error class, automatic tempdir cleanup.
"""

from __future__ import annotations

import sys

from scitex_agentic_journal._gate1 import GateFailure, cloned_code_repo


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: 02_gate1_code_repo_clone.py <repo-url>")
        return 2
    repo_url = sys.argv[1]
    try:
        with cloned_code_repo(repo_url) as repo:
            print(f"GATE-1 PASS — cloned {repo.repo_url}")
            print(f"  on-disk path : {repo.path}")
            print(f"  HEAD commit  : {repo.head_commit}")
            print(f"  HEAD subject : {repo.head_subject}")
    except GateFailure as fail:
        print(f"GATE-1 FAIL: {fail}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
