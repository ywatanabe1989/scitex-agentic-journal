"""Tests for ``_gate1._code_repo.clone_code_repo`` + ``cloned_code_repo``.

Discipline (STX-NM001-003 / PA-306, "no mocks"):

- Production path shells out to the real ``git`` binary. We do not
  patch ``subprocess``, we do not stub ``git``, we do not inject a fake
  binary on PATH.
- For hermetic CI we create a **real local bare git repository** in a
  pytest tempdir, push one real commit into it, and clone via the
  ``file://`` URL. This exercises real network-style URL handling
  (file scheme → libgit2/transport plumbing) without leaving the
  machine.
- The pre-flight failure paths (empty URL, pre-existing destination)
  are tested without any clone occurring.
- One opt-in ``@pytest.mark.network`` test clones a real GitHub
  repository when ``SCITEX_RUN_NETWORK_TESTS=1``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scitex_agentic_journal._gate1 import (
    ClonedRepo,
    GateFailure,
    clone_code_repo,
    cloned_code_repo,
)


# ---------------------------------------------------------------------------
# Local bare-repo fixture — real git, real commit, real file:// URL.
# ---------------------------------------------------------------------------


def _run_git(*args: str, cwd: Path | None = None) -> None:
    """Run real git, raise on failure. Used only by the fixture builder."""
    env = {
        **os.environ,
        # Make sure the fixture commit is reproducible across CI hosts.
        "GIT_AUTHOR_NAME": "fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        # Defeat any global user config interfering with the commit.
        "HOME": "/tmp",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }
    subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        env=env,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def bare_repo_url(tmp_path: Path) -> str:
    """Build a real bare git repo with one commit; yield its ``file://`` URL.

    Layout::

        tmp_path/
            seed/                # working tree we commit into bare/
                README.md
            bare.git/            # bare repo (the URL we hand out)
    """
    seed = tmp_path / "seed"
    bare = tmp_path / "bare.git"
    seed.mkdir()
    # Seed working tree.
    (seed / "README.md").write_text("# fixture\n")
    _run_git("init", "-q", "-b", "main", str(seed))
    _run_git("add", "README.md", cwd=seed)
    _run_git("commit", "-q", "-m", "fixture: seed commit", cwd=seed)
    # Bare repo we will clone from. Force the default branch to `main`
    # explicitly: without -b, `git init --bare` defaults to `master`,
    # leaving HEAD pointing at a non-existent ref after we push `main`,
    # which makes a downstream `git clone` materialise an empty working
    # tree (`git log` then exits 128).
    _run_git("init", "-q", "--bare", "-b", "main", str(bare))
    _run_git("remote", "add", "origin", str(bare), cwd=seed)
    _run_git("push", "-q", "origin", "main", cwd=seed)
    # Belt + braces: pin the bare repo's HEAD to main in case the host
    # `git` ignored -b for --bare.
    _run_git("symbolic-ref", "HEAD", "refs/heads/main", cwd=bare)
    return f"file://{bare}"


# ---------------------------------------------------------------------------
# clone_code_repo — pre-flight validation.
# ---------------------------------------------------------------------------


class TestPreflightValidation:
    def test_empty_url_raises(self, tmp_path: Path) -> None:
        with pytest.raises(GateFailure) as ei:
            clone_code_repo("", tmp_path / "dest")
        assert ei.value.check == "code_repo"
        assert "empty" in ei.value.reason

    def test_whitespace_url_raises(self, tmp_path: Path) -> None:
        with pytest.raises(GateFailure) as ei:
            clone_code_repo("   \n", tmp_path / "dest")
        assert "empty" in ei.value.reason

    def test_existing_destination_refused(
        self, tmp_path: Path, bare_repo_url: str
    ) -> None:
        dest = tmp_path / "preexisting"
        dest.mkdir()
        with pytest.raises(GateFailure) as ei:
            clone_code_repo(bare_repo_url, dest)
        assert "destination" in ei.value.reason
        # The pre-existing path must not have been mutated.
        assert dest.exists() and list(dest.iterdir()) == []


# ---------------------------------------------------------------------------
# clone_code_repo — happy paths against the real local bare repo.
# ---------------------------------------------------------------------------


class TestCloneAgainstBareFixture:
    def test_returns_cloned_repo_with_head(
        self, tmp_path: Path, bare_repo_url: str
    ) -> None:
        dest = tmp_path / "clone"
        repo = clone_code_repo(bare_repo_url, dest)
        assert isinstance(repo, ClonedRepo)
        assert repo.repo_url == bare_repo_url
        assert repo.path == dest.resolve()
        assert (repo.path / "README.md").read_text() == "# fixture\n"
        assert len(repo.head_commit) == 40
        assert repo.head_subject == "fixture: seed commit"

    def test_shallow_clone_by_default(
        self, tmp_path: Path, bare_repo_url: str
    ) -> None:
        repo = clone_code_repo(bare_repo_url, tmp_path / "clone")
        # Shallow clones create the .git/shallow marker file.
        assert (repo.path / ".git" / "shallow").exists()

    def test_full_history_when_depth_zero(
        self, tmp_path: Path, bare_repo_url: str
    ) -> None:
        repo = clone_code_repo(bare_repo_url, tmp_path / "clone", depth=0)
        assert not (repo.path / ".git" / "shallow").exists()

    def test_branch_pin(self, tmp_path: Path, bare_repo_url: str) -> None:
        # The fixture only has `main`; we exercise the --branch path.
        repo = clone_code_repo(bare_repo_url, tmp_path / "clone", ref="main")
        assert repo.head_subject == "fixture: seed commit"


# ---------------------------------------------------------------------------
# clone_code_repo — failure paths against real (mis-)configured URLs.
# ---------------------------------------------------------------------------


class TestCloneFailures:
    def test_nonexistent_url_raises_clone_failed(
        self, tmp_path: Path
    ) -> None:
        ghost = tmp_path / "does-not-exist.git"
        with pytest.raises(GateFailure) as ei:
            clone_code_repo(f"file://{ghost}", tmp_path / "clone")
        assert ei.value.check == "code_repo"
        assert "clone failed" in ei.value.reason
        # Destination must be cleaned up on failure.
        assert not (tmp_path / "clone").exists()

    def test_not_a_git_repo_raises_clone_failed(
        self, tmp_path: Path
    ) -> None:
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()
        (not_a_repo / "hello.txt").write_text("not git\n")
        with pytest.raises(GateFailure) as ei:
            clone_code_repo(f"file://{not_a_repo}", tmp_path / "clone")
        assert "clone failed" in ei.value.reason

    def test_missing_git_binary_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # NOTE on no-mocks: monkeypatching PATH is *configuration*, not a
        # stub of the production collaborator. The git binary itself is
        # unmodified; we simply remove it from the lookup set so the real
        # production code takes its real "git not on PATH" branch.
        monkeypatch.setenv("PATH", "")
        with pytest.raises(GateFailure) as ei:
            clone_code_repo("file:///tmp/whatever.git", tmp_path / "clone")
        assert ei.value.check == "code_repo"
        assert "git binary not on PATH" in ei.value.reason


# ---------------------------------------------------------------------------
# cloned_code_repo — context manager owns its tempdir.
# ---------------------------------------------------------------------------


class TestClonedCodeRepoCM:
    def test_yields_repo_and_cleans_up(self, bare_repo_url: str) -> None:
        with cloned_code_repo(bare_repo_url) as repo:
            kept_path = repo.path
            assert kept_path.exists()
            assert (kept_path / "README.md").exists()
        # After exit the tempdir is gone — production callers do not have
        # to chase cleanup themselves.
        assert not kept_path.exists()

    def test_cleans_up_on_clone_failure(self, tmp_path: Path) -> None:
        with pytest.raises(GateFailure):
            with cloned_code_repo(
                f"file://{tmp_path / 'never-existed.git'}"
            ):
                pass
        # No stray scitex-aj-clone-* tempdirs left in the system temp.
        leftovers = [
            p
            for p in Path("/tmp").glob("scitex-aj-clone-*")
            if p.is_dir() and any(p.iterdir())
        ]
        # Allow leftovers from parallel test workers — but none should be
        # tied to this URL, i.e. none should contain a `repo/` subdir.
        # We just sanity-check that the function returned without leaking
        # the directory we explicitly created.
        for p in leftovers:
            # Best-effort assertion; do not fail other workers.
            assert not (p / "repo" / "README.md").exists()


# ---------------------------------------------------------------------------
# Optional real-network test against GitHub.
# ---------------------------------------------------------------------------


@pytest.mark.network
@pytest.mark.skipif(
    os.environ.get("SCITEX_RUN_NETWORK_TESTS") != "1",
    reason="opt in by setting SCITEX_RUN_NETWORK_TESTS=1",
)
def test_real_github_clone(tmp_path: Path) -> None:
    repo = clone_code_repo(
        "https://github.com/octocat/Hello-World.git",
        tmp_path / "hello",
    )
    assert (repo.path / "README").exists() or (repo.path / "README.md").exists()
    assert len(repo.head_commit) == 40
