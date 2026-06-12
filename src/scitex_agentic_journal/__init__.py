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

__all__ = ["__version__"]
