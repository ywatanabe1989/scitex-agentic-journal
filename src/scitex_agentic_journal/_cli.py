"""Top-level CLI for ``scitex-agentic-journal``.

Console script entry point declared in ``pyproject.toml``::

    [project.scripts]
    scitex-agentic-journal = "scitex_agentic_journal._cli:main"

Subcommands map to the M1+ pipeline stages and are wired up
incrementally as the relevant issues land:

- ``submit``  — gate-1 submission orchestrator (issue #5).
- ``review``  — single reviewer-agent harness (issue #6).
- ``decide``  — editorial decision engine (issue #7).
- ``publish`` — Live Paper hand-off (issue #9).

Until those land, each subcommand raises a structured
:class:`click.ClickException` pointing at its tracking issue, so the
operator gets an actionable error rather than a stub no-op.
"""

from __future__ import annotations

import click

from scitex_agentic_journal import __version__


@click.group(
    help=(
        "ARA-native AI-reviewed open publishing on top of Clew. "
        "See `scitex-agentic-journal <subcommand> --help`."
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    __version__, "--version", "-V", prog_name="scitex-agentic-journal"
)
def main() -> None:
    """Entry point for the ``scitex-agentic-journal`` console script."""


@main.command(name="submit")
@click.argument(
    "bundle_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def submit(bundle_dir: str) -> None:
    """Submit a manuscript bundle through Gate-1 (orchestrator stub).

    The wiring of Gate-1 components (#2 ORCID, #3 code repo, #4 Clew
    DAG) into a single CLI verdict is tracked by issue #5 (M1 CLI).
    """
    raise click.ClickException(
        "M1 CLI orchestrator is not implemented yet — see issue #5 "
        f"(bundle_dir={bundle_dir!r})."
    )


@main.command(name="review")
@click.argument("submission_id")
def review(submission_id: str) -> None:
    """Run a single reviewer-agent against a persisted submission."""
    raise click.ClickException(
        "M2 reviewer-agent harness is not implemented yet — see issue #6 "
        f"(submission_id={submission_id!r})."
    )


@main.command(name="decide")
@click.argument("submission_id")
def decide(submission_id: str) -> None:
    """Apply the editorial decision engine to a review record."""
    raise click.ClickException(
        "M3 decision engine is not implemented yet — see issue #7 "
        f"(submission_id={submission_id!r})."
    )


@main.command(name="publish")
@click.argument("submission_id")
def publish(submission_id: str) -> None:
    """Hand off an accepted submission to scitex-live-paper."""
    raise click.ClickException(
        "M5 publish hand-off is not implemented yet — see issue #9 "
        f"(submission_id={submission_id!r})."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
