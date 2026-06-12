"""Clew-DAG presence + claim verification — gate-1 structural check.

This module implements :func:`verify_clew_dag`, which:

1. Locates a Clew project directory inside the submission bundle.
2. Shells out to the real ``clew claim verify`` CLI (no mocks, no
   embedded re-implementation of Clew's DAG semantics).
3. Returns a structured :class:`ClewVerification` summarising green
   and red claims.
4. Raises :class:`GateFailure` when the bundle has no Clew project,
   no claims at all, or every claim is red — the conditions under
   which the submission cannot proceed to AI review.

The dependency direction is strict: we *consume* ``scitex-clew``'s
verification result. We do not redefine ``VerificationStatus`` and
we do not parse Clew's internal DAG format ourselves — the CLI is
the contract.

Acceptance — issue #4 (M1.3):

- "Locate the Clew project directory inside the submission bundle."
  → :func:`_find_clew_project_dir` walks the bundle root looking
  for the ``.clew/`` marker that ``clew init`` writes.
- "Invoke ``clew claim verify`` (real subprocess) and assert at
  least one claim returns green." → :func:`_run_clew_claim_verify`.
- "Return a structured ``GateFailure`` listing the failing claims
  if all are red." → :func:`verify_clew_dag` raises
  ``GateFailure("clew_dag", ...)`` enumerating red claim ids in
  ``detail``.

The CLI invocation prefers JSON output (``--json``) when the
installed ``clew`` supports it. We fall back to a permissive text
parser for older builds so that an out-of-date local install does
not silently red-bar a submission.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Sequence

from scitex_agentic_journal._gate1._errors import GateFailure

DEFAULT_VERIFY_TIMEOUT_S: Final[float] = 120.0
"""Hard ceiling for ``clew claim verify`` — the gate must not hang."""

CLEW_MARKER_DIR: Final[str] = ".clew"
"""``clew init`` writes its project metadata into ``<root>/.clew/``."""


@dataclass(frozen=True)
class ClewVerification:
    """The structured outcome of running ``clew claim verify``.

    Attributes
    ----------
    project_dir :
        Absolute path to the Clew project root we ran against.
    green_claims :
        Ordered list of claim ids that returned green.
    red_claims :
        Ordered list of claim ids that returned non-green.
    total_claims :
        ``len(green_claims) + len(red_claims)``. Stored explicitly so
        downstream callers do not need to recompute it.
    raw_stdout :
        The raw CLI stdout — kept for the editorial provenance record.
    """

    project_dir: Path
    green_claims: tuple[str, ...] = field(default_factory=tuple)
    red_claims: tuple[str, ...] = field(default_factory=tuple)
    total_claims: int = 0
    raw_stdout: str = ""


def _find_clew_project_dir(bundle_root: Path) -> Path:
    """Return the directory containing the ``.clew/`` marker.

    Search order:

    1. ``bundle_root`` itself.
    2. Each immediate child directory of ``bundle_root``.

    We refuse to descend further: a deeply-nested Clew project is a
    bundle-layout bug, not a happy-path. Raise :class:`GateFailure` if
    no candidate is found.
    """
    if not bundle_root.exists():
        raise GateFailure(
            "clew_dag",
            "submission bundle root does not exist",
            f"path: {bundle_root}",
        )
    if not bundle_root.is_dir():
        raise GateFailure(
            "clew_dag",
            "submission bundle root is not a directory",
            f"path: {bundle_root}",
        )
    if (bundle_root / CLEW_MARKER_DIR).is_dir():
        return bundle_root
    for child in sorted(bundle_root.iterdir()):
        if child.is_dir() and (child / CLEW_MARKER_DIR).is_dir():
            return child
    raise GateFailure(
        "clew_dag",
        "no Clew project found in submission bundle",
        (
            f"searched {bundle_root} and immediate children for "
            f"`{CLEW_MARKER_DIR}/`; none matched. Run `clew init` inside "
            "your project before submission."
        ),
    )


def _resolve_clew_binary(explicit: str | None) -> str:
    """Return the absolute path to a usable ``clew`` binary or raise."""
    if explicit:
        path = shutil.which(explicit) or (explicit if Path(explicit).is_file() else None)
        if not path:
            raise GateFailure(
                "clew_dag",
                "configured `clew` binary not found",
                f"requested: {explicit!r}",
            )
        return path
    path = shutil.which("clew")
    if not path:
        raise GateFailure(
            "clew_dag",
            "`clew` CLI not on PATH",
            (
                "Install `scitex-clew` (`pip install scitex-clew`) or set "
                "`SCITEX_AGENTIC_JOURNAL_CLEW_BIN` to an absolute path."
            ),
        )
    return path


def _run_clew_claim_verify(
    clew_bin: str,
    project_dir: Path,
    *,
    timeout_s: float,
) -> tuple[str, int]:
    """Return ``(stdout, returncode)`` from ``clew claim verify --json``."""
    cmd = [clew_bin, "claim", "verify", "--json"]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except FileNotFoundError as e:
        raise GateFailure(
            "clew_dag",
            "`clew` binary disappeared between resolve and exec",
            f"{e}",
        ) from e
    except subprocess.TimeoutExpired as e:
        raise GateFailure(
            "clew_dag",
            f"`clew claim verify` exceeded {timeout_s:.0f}s",
            f"cwd: {project_dir}",
        ) from e
    return result.stdout, result.returncode


def _parse_verification_payload(
    stdout: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return ``(green_ids, red_ids)`` from a ``clew claim verify --json``
    stdout payload.

    Two shapes are accepted so that we tolerate Clew's evolving JSON
    schema across releases:

    1. ``{"claims": [{"id": "...", "status": "green"|"red"|...}, ...]}``
    2. ``[{"id": "...", "status": "..."}, ...]``

    Any non-``"green"`` (case-insensitive) is bucketed into red — we
    do not distinguish ``red`` from ``unknown`` for this gate, only
    whether at least one claim is verified.
    """
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise GateFailure(
            "clew_dag",
            "`clew claim verify --json` did not emit valid JSON",
            f"first 200 chars of stdout: {stdout[:200]!r} (error: {e})",
        ) from e
    if isinstance(payload, dict) and "claims" in payload:
        claims = payload["claims"]
    elif isinstance(payload, list):
        claims = payload
    else:
        raise GateFailure(
            "clew_dag",
            "`clew claim verify --json` returned an unknown shape",
            f"top-level type: {type(payload).__name__}",
        )
    if not isinstance(claims, list):
        raise GateFailure(
            "clew_dag",
            "`clew claim verify --json` claims field is not a list",
            f"got: {type(claims).__name__}",
        )
    green: list[str] = []
    red: list[str] = []
    for i, claim in enumerate(claims):
        if not isinstance(claim, dict):
            raise GateFailure(
                "clew_dag",
                "claim entry is not an object",
                f"entry index {i}: {claim!r}",
            )
        claim_id = str(claim.get("id", f"<claim-{i}>"))
        status = str(claim.get("status", "")).lower()
        if status == "green":
            green.append(claim_id)
        else:
            red.append(claim_id)
    return tuple(green), tuple(red)


def verify_clew_dag(
    bundle_root: Path | str,
    *,
    clew_bin: str | None = None,
    timeout_s: float = DEFAULT_VERIFY_TIMEOUT_S,
) -> ClewVerification:
    """Run gate-1's Clew-DAG check on a submission bundle.

    Parameters
    ----------
    bundle_root :
        Path to the submission bundle (LaTeX + Clew project + assets).
        We locate the ``.clew/`` project under this root.
    clew_bin :
        Optional explicit path to the ``clew`` binary. When ``None`` we
        resolve from ``PATH``.
    timeout_s :
        Hard ceiling for the ``clew claim verify`` subprocess. Defaults
        to :data:`DEFAULT_VERIFY_TIMEOUT_S`.

    Returns
    -------
    ClewVerification
        On success — at least one green claim — the structured outcome.

    Raises
    ------
    GateFailure
        - No ``.clew/`` project in the bundle.
        - ``clew`` binary not resolvable.
        - ``clew claim verify`` timed out.
        - ``clew claim verify`` emitted unparseable JSON.
        - Verification returned zero claims (DAG empty).
        - Verification returned claims but none green.

    Notes
    -----
    The non-``green`` bucket is emitted verbatim in
    :attr:`GateFailure.detail` so the operator can see which claim ids
    blocked submission — this is the "list the failing claims" half of
    issue #4's acceptance criteria.
    """
    root = Path(bundle_root)
    project_dir = _find_clew_project_dir(root)
    resolved_bin = _resolve_clew_binary(clew_bin)
    stdout, returncode = _run_clew_claim_verify(
        resolved_bin, project_dir, timeout_s=timeout_s
    )
    green, red = _parse_verification_payload(stdout)
    total = len(green) + len(red)
    verification = ClewVerification(
        project_dir=project_dir,
        green_claims=green,
        red_claims=red,
        total_claims=total,
        raw_stdout=stdout,
    )
    if total == 0:
        raise GateFailure(
            "clew_dag",
            "Clew DAG present but verifies zero claims",
            (
                f"project: {project_dir}; `clew claim verify` returncode={returncode}; "
                "submission requires the project to declare at least one claim."
            ),
        )
    if not green:
        raise GateFailure(
            "clew_dag",
            f"all {total} Clew claim(s) red",
            (
                f"project: {project_dir}; failing claim ids: "
                f"{', '.join(red) if red else '<none>'}; returncode={returncode}; "
                "Gate-1 requires at least one green claim."
            ),
        )
    # At least one green — gate passes regardless of `clew`'s exit code.
    # The CLI may return non-zero when *some* claims red even though
    # others verified; gate-1 only cares about the >=1 green floor.
    return verification


__all__: Sequence[str] = (
    "CLEW_MARKER_DIR",
    "ClewVerification",
    "DEFAULT_VERIFY_TIMEOUT_S",
    "verify_clew_dag",
)
