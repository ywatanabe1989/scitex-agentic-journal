# Examples

Runnable examples for `scitex-agentic-journal`.

The package is in **pre-alpha**. End-to-end pipeline examples (submit →
agent review → decide → publish) land alongside the M1 CLI orchestrator
(issue #5) and the M2 reviewer-agent harness (issue #6). Until then the
examples below cover the small public surface that already exists.

## Gate-1 ORCID resolvability check (issue #2)

```python
from scitex_agentic_journal._gate1 import verify_orcid, GateFailure

try:
    rec = verify_orcid("0000-0002-1825-0097")
    print(rec.display_name, "->", rec.orcid_id)
except GateFailure as fail:
    print(fail)
```

## Gate-1 code-repo cloneability (issue #3)

```python
from scitex_agentic_journal._gate1 import cloned_code_repo, GateFailure

try:
    with cloned_code_repo(
        "https://github.com/octocat/Hello-World.git"
    ) as repo:
        print("HEAD at", repo.head_commit, "—", repo.head_subject)
except GateFailure as fail:
    print(fail)
```

## CLI smoke

```console
$ scitex-agentic-journal --version
scitex-agentic-journal, version <X.Y.Z>
$ scitex-agentic-journal --help
Usage: scitex-agentic-journal [OPTIONS] COMMAND [ARGS]...
```

Subcommands (`submit`, `review`, `decide`, `publish`) currently raise a
structured `ClickException` pointing at their tracking issue.
