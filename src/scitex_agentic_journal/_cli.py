"""Top-level CLI for ``scitex-agentic-journal``.

Console script entry point declared in ``pyproject.toml``::

    [project.scripts]
    scitex-agentic-journal = "scitex_agentic_journal._cli:main"

Top-level conventions (audited by ``scitex-dev ecosystem audit-all``):

- A canonical opening line ``scitex-agentic-journal (vX.Y.Z) — …`` is
  printed in ``--help`` so the user sees the active version without
  needing ``--version``.
- ``--json`` is a universal flag for machine-readable output. Today it
  switches the help epilog into a JSON shape; subcommands inherit the
  flag and will switch their own output format as they get implemented.
- ``--help-recursive`` prints the full subcommand tree's help so
  agents can introspect the surface in one call.
- Mutating verbs (``publish``) carry ``--dry-run`` and ``--yes/-y``.
- A ``config-path`` fallback is documented in the help epilog so the
  audit's §6b rule passes (we mention ``$SCITEX_AGENTIC_JOURNAL_CONFIG``
  and ``~/.scitex/agentic-journal/config.yaml``).
- ``info list-python-apis`` enumerates the importable Python surface
  (§1a). ``mcp list-tools`` enumerates the MCP tools that the optional
  ``[mcp]`` extra exposes (§1a); today the list is empty until the
  MCP server lands post-MVP.

Until the M1+ issues land, each pipeline subcommand raises a structured
:class:`click.ClickException` pointing at its tracking issue so the
operator gets an actionable error rather than a stub no-op.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import sys
from typing import Iterable

import click

from scitex_agentic_journal import __version__

_CANONICAL_HEADER = (
    f"scitex-agentic-journal (v{__version__}) — ARA-native AI-reviewed "
    "open publishing on top of Clew."
)

# IMPORTANT: keep the literal ``v{__version__}`` token here so the
# audit's ``--help`` parser (§4 `_check_root_help_has_version`) sees a
# `vX.Y.Z` token in either ``cmd.help`` or ``cmd.epilog``. The token
# is fed by ``importlib.metadata.version()`` via ``__version__`` so it
# always tracks the installed distribution.
_HELP_EPILOG = (
    f"scitex-agentic-journal v{__version__}. "
    "Configuration is read from $SCITEX_AGENTIC_JOURNAL_CONFIG, then "
    "./config.yaml, then ~/.scitex/agentic-journal/config.yaml. Run "
    "`scitex-agentic-journal --help-recursive` for the full subcommand "
    "tree. Add `--json` for machine-readable output."
)


def _emit_help_recursive(ctx: click.Context) -> None:
    """Print the full subcommand tree's help text to stdout."""
    root_cmd = ctx.find_root().command
    root_info = ctx.find_root().info_name or "scitex-agentic-journal"

    def _walk(cmd: click.Command, name_path: list[str]) -> None:
        with click.Context(cmd, info_name=name_path[-1], parent=None) as sub_ctx:
            click.echo("$ " + " ".join(name_path) + " --help")
            click.echo(cmd.get_help(sub_ctx))
            click.echo("")
            if isinstance(cmd, click.Group):
                for child_name in sorted(cmd.commands):
                    child = cmd.commands[child_name]
                    if getattr(child, "hidden", False):
                        continue
                    _walk(child, name_path + [child_name])

    _walk(root_cmd, [root_info])


def _emit_help_json(cmd: click.Command, name: str) -> None:
    """Print the help payload as JSON for agent / tool consumption."""

    def _serialise(c: click.Command, cmd_name: str) -> dict:
        with click.Context(c, info_name=cmd_name, parent=None) as sub_ctx:
            payload: dict = {
                "name": cmd_name,
                "help": c.get_short_help_str(),
                "version": __version__,
                "params": [
                    {
                        "name": p.name,
                        "opts": list(getattr(p, "opts", []) or []),
                        "help": getattr(p, "help", None) or "",
                        "is_flag": bool(getattr(p, "is_flag", False)),
                        "required": bool(getattr(p, "required", False)),
                    }
                    for p in c.get_params(sub_ctx)
                ],
            }
            if isinstance(c, click.Group):
                payload["subcommands"] = [
                    _serialise(c.commands[name], name)
                    for name in sorted(c.commands)
                    if not getattr(c.commands[name], "hidden", False)
                ]
            return payload

    click.echo(json.dumps(_serialise(cmd, name), indent=2))


class _AgenticJournalGroup(click.Group):
    """Click group that prepends the canonical header to ``--help``.

    Audit §4 expects the very first line of ``--help`` to identify the
    tool and its active version. Click's default ``format_help`` opens
    with ``Usage:`` so we override ``format_help_text`` to inject the
    canonical line.
    """

    def format_help_text(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        formatter.write_paragraph()
        formatter.write_text(_CANONICAL_HEADER)
        formatter.write_paragraph()
        super().format_help_text(ctx, formatter)


@click.group(
    cls=_AgenticJournalGroup,
    help=(
        "ARA-native AI-reviewed open publishing on top of Clew. "
        "See `scitex-agentic-journal <subcommand> --help`."
    ),
    epilog=_HELP_EPILOG,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(
    __version__, "--version", "-V", prog_name="scitex-agentic-journal"
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help=(
        "Emit help / status output as JSON so agents and other tools "
        "can parse it. Subcommands inherit this flag and switch their "
        "output format when they ship."
    ),
)
@click.option(
    "--help-recursive",
    "help_recursive",
    is_flag=True,
    default=False,
    help=(
        "Print --help for every subcommand of the tree, in order, so "
        "agents can introspect the full surface in one call."
    ),
)
@click.pass_context
def main(ctx: click.Context, as_json: bool, help_recursive: bool) -> None:
    """Entry point for the ``scitex-agentic-journal`` console script."""
    ctx.ensure_object(dict)
    ctx.obj["as_json"] = as_json
    ctx.obj["help_recursive"] = help_recursive
    if help_recursive:
        _emit_help_recursive(ctx)
        ctx.exit(0)
    if as_json and ctx.invoked_subcommand is None:
        _emit_help_json(ctx.command, ctx.info_name or "scitex-agentic-journal")
        ctx.exit(0)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


@main.command(name="submit")
@click.argument(
    "bundle_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def submit(bundle_dir: str) -> None:
    """Submit a manuscript bundle through Gate-1.

    Loads ``<bundle>/bundle.yaml``, runs the three structural checks
    (ORCID #2, code-repo #3, Clew DAG #4) in declared order, persists
    the verdict under ``$SCITEX_AGENTIC_JOURNAL_HOME/submissions/<id>/``,
    and prints ``GATE-1 PASS submission_id=...`` on success.

    On any structural failure prints a single-line ``GATE-1 FAIL
    [<check>]: <reason> -- <detail>`` and exits non-zero, with no
    Python traceback.

    Example:

      $ scitex-agentic-journal submit ./paper/
      GATE-1 PASS submission_id=sub_2026_06_13_abc123
    """
    from scitex_agentic_journal._submit import (
        Gate1Failure,
        SubmissionLoadError,
        load_submission,
        persist_verdict,
        run_gate1,
    )

    try:
        submission = load_submission(bundle_dir)
    except SubmissionLoadError as e:
        raise click.ClickException(str(e)) from e
    try:
        verdict = run_gate1(submission)
    except Gate1Failure as f:
        # `GateFailure.__str__` already produces the canonical
        # `GATE-1 FAIL [<check>]: <reason> -- <detail>` line.
        raise click.ClickException(str(f.wrapped)) from f
    persisted = persist_verdict(verdict)
    click.echo(f"GATE-1 PASS submission_id={persisted.submission_id}")


@main.command(name="review")
@click.argument("submission_id")
def review(submission_id: str) -> None:
    """Run a single reviewer-agent against a persisted submission.

    Example:

      $ scitex-agentic-journal review sub_2026_06_12_abc123
    """
    raise click.ClickException(
        "M2 reviewer-agent harness is not implemented yet — see issue #6 "
        f"(submission_id={submission_id!r})."
    )


@main.command(name="decide")
@click.argument("submission_id")
def decide(submission_id: str) -> None:
    """Apply the editorial decision engine to a review record.

    Example:

      $ scitex-agentic-journal decide sub_2026_06_12_abc123
    """
    raise click.ClickException(
        "M3 decision engine is not implemented yet — see issue #7 "
        f"(submission_id={submission_id!r})."
    )


@main.command(name="publish")
@click.argument("submission_id")
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    show_default=True,
    help=(
        "Compute the publish bundle but do not stamp a persistent ID "
        "and do not hand off to scitex-live-paper. Mutating verbs MUST "
        "support --dry-run."
    ),
)
@click.option(
    "--yes",
    "-y",
    "assume_yes",
    is_flag=True,
    default=False,
    help=(
        "Assume yes to confirmation prompts. Mutating verbs MUST "
        "support --yes / -y for non-interactive callers."
    ),
)
def publish(
    submission_id: str, dry_run: bool, assume_yes: bool
) -> None:
    """Hand off an accepted submission to scitex-live-paper.

    Example:

      $ scitex-agentic-journal publish sub_2026_06_12_abc123 --dry-run
      $ scitex-agentic-journal publish sub_2026_06_12_abc123 --yes
    """
    raise click.ClickException(
        "M5 publish hand-off is not implemented yet — see issue #9 "
        f"(submission_id={submission_id!r}, "
        f"dry_run={dry_run!r}, yes={assume_yes!r})."
    )


@main.command(name="list-python-apis")
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="Increase verbosity (-v, -vv, -vvv).",
)
@click.option(
    "--json",
    "as_json_local",
    is_flag=True,
    default=False,
    help=(
        "Emit machine-readable JSON output. Required by §1a / §2 for "
        "every `list` verb (read verbs MUST support --json)."
    ),
)
@click.pass_context
def list_python_apis(
    ctx: click.Context, verbose: int, as_json_local: bool
) -> None:
    """List every importable Python API exposed by this package.

    The audit (§1a) requires this command at the top level so agents
    can discover the public surface without combing the source tree.

    Example:

      $ scitex-agentic-journal list-python-apis
      $ scitex-agentic-journal list-python-apis -vv --json
    """
    del verbose  # currently unused; accepted for ecosystem-CLI parity.
    apis = list(_iter_python_api_names("scitex_agentic_journal"))
    apis.sort()
    root_obj = ctx.find_root().obj or {}
    if as_json_local or root_obj.get("as_json"):
        click.echo(json.dumps({"apis": apis}, indent=2))
        return
    for name in apis:
        click.echo(name)


def _iter_python_api_names(root_pkg: str) -> Iterable[str]:
    """Yield ``module:name`` strings for every public symbol under ``root_pkg``."""
    try:
        pkg = importlib.import_module(root_pkg)
    except ImportError:
        return
    yield from _public_names(pkg)
    pkg_path = getattr(pkg, "__path__", None)
    if pkg_path is None:
        return
    for info in pkgutil.walk_packages(pkg_path, prefix=f"{root_pkg}."):
        # Skip private modules; the public surface is what we audit.
        leaf = info.name.rsplit(".", 1)[-1]
        if leaf.startswith("_") and leaf != "__init__":
            # Allow modules whose name starts with one underscore (the
            # SciTeX convention for "internal package, re-exported via
            # the package __init__") — but skip dunder modules.
            if leaf.startswith("__"):
                continue
        try:
            mod = importlib.import_module(info.name)
        except Exception:  # pragma: no cover - best-effort introspection
            continue
        yield from _public_names(mod)


def _public_names(mod) -> Iterable[str]:
    explicit = getattr(mod, "__all__", None)
    if explicit:
        for name in explicit:
            yield f"{mod.__name__}:{name}"
        return
    for name in vars(mod):
        if name.startswith("_"):
            continue
        yield f"{mod.__name__}:{name}"


@main.group(name="mcp")
def mcp() -> None:
    """MCP server commands (optional ``[mcp]`` extra)."""


@mcp.command(name="list-tools")
@click.option(
    "--json",
    "as_json_local",
    is_flag=True,
    default=False,
    help=(
        "Emit machine-readable JSON output. Required by §1a / §2 for "
        "every `list` verb."
    ),
)
@click.pass_context
def mcp_list_tools(ctx: click.Context, as_json_local: bool) -> None:
    """List the MCP tools this package exposes.

    Today the list is empty: the MCP server lands post-MVP. The
    command itself is mandatory (audit §1a) so agents can probe for
    capabilities without a try/except on the subcommand name.

    Example:

      $ scitex-agentic-journal mcp list-tools
      $ scitex-agentic-journal mcp list-tools --json
    """
    tools: list[str] = []
    root_obj = ctx.find_root().obj or {}
    if as_json_local or root_obj.get("as_json"):
        click.echo(json.dumps({"tools": tools}, indent=2))
        return
    if not tools:
        click.echo("(no MCP tools registered — see post-MVP roadmap)")
        return
    for tool in tools:  # pragma: no cover - reached when tools exist
        click.echo(tool)


# ---------------------------------------------------------------------------
# `skills` command group (§1a). The package ships a bundled
# `_skills/scitex-agentic-journal/` tree, so the audit's §1a rule
# requires a `<pkg> skills {list, get, install}` Click sub-group.
# The implementation lives in `_cli_skills` to keep this module under
# the harness's per-file line ceiling.
# ---------------------------------------------------------------------------

from scitex_agentic_journal._cli_skills import register_skills_commands

register_skills_commands(main)


# ---------------------------------------------------------------------------
# Shell completion (install-shell-completion + print-shell-completion).
#
# The audit (§1a) requires both commands at the top level so
# `<pkg> <TAB>` produces something. We wire them via the canonical
# helper exposed by scitex-dev. If for any reason scitex-dev is not
# importable in this environment, we degrade to local stubs that
# return the same exit codes so the surface stays present and
# discoverable by agents (the install path itself is a no-op in that
# fallback).
# ---------------------------------------------------------------------------

try:
    from scitex_dev._cli._completion import attach_shell_completion

    attach_shell_completion(main, prog_name="scitex-agentic-journal")
except Exception:  # pragma: no cover - degraded path

    @main.command(name="print-shell-completion")
    @click.argument(
        "shell",
        type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    )
    def print_shell_completion(shell: str) -> None:
        """Print the shell-completion script (degraded fallback).

        Wires via `scitex_dev._cli._completion.attach_shell_completion`
        when scitex-dev is importable; this fallback stub keeps the
        command surface present so agents introspecting the CLI do not
        see it disappear.

        Example:

          $ scitex-agentic-journal print-shell-completion bash
        """
        click.echo(
            f"# scitex-dev._cli._completion is not available — "
            f"completion script for {shell} unavailable in this env."
        )

    @main.command(name="install-shell-completion")
    @click.argument(
        "shell",
        type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    )
    @click.option(
        "--dry-run/--no-dry-run",
        default=False,
        show_default=True,
        help="Print what would be done without modifying the shell config.",
    )
    @click.option(
        "--yes",
        "-y",
        "assume_yes",
        is_flag=True,
        default=False,
        help="Assume yes to confirmation prompts.",
    )
    def install_shell_completion(
        shell: str, dry_run: bool, assume_yes: bool
    ) -> None:
        """Install the shell-completion script (degraded fallback).

        Example:

          $ scitex-agentic-journal install-shell-completion bash --dry-run
          $ scitex-agentic-journal install-shell-completion zsh --yes
        """
        del dry_run, assume_yes
        raise click.ClickException(
            "scitex-dev._cli._completion is not importable — install "
            f"`scitex-dev` to enable shell-completion install for {shell}."
        )


if __name__ == "__main__":  # pragma: no cover
    main()
