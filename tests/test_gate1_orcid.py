"""Tests for ``_gate1._orcid.verify_orcid``.

Discipline (STX-NM001-003 / PA-306, "no mocks"):

- The production path stays real HTTP via ``requests``. We never patch
  ``requests``, never use a respx/responses-style replay library, and
  never inject a fake session object.
- For hermetic CI we spin up a **real local HTTP server** (stdlib
  ``http.server`` on an ephemeral port) that serves real JSON files
  out of ``tests/_fixtures/``. The resolver hits it over real TCP via
  the legitimate ``base_url`` config seam that the CLI will also use
  (e.g. to point at ``sandbox.orcid.org``).
- One test (``test_real_orcid_org_resolves``) talks to the real
  ``pub.orcid.org``; it is marked ``@pytest.mark.network`` and skipped
  unless ``SCITEX_RUN_NETWORK_TESTS=1``.
"""

from __future__ import annotations

import json
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Iterator

import pytest

from scitex_agentic_journal._gate1 import GateFailure, OrcidRecord, verify_orcid
from scitex_agentic_journal._gate1._orcid import normalize_orcid

FIXTURE_DIR = Path(__file__).parent / "_fixtures"


# ---------------------------------------------------------------------------
# Local fixture HTTP server — real TCP, real HTTP, real ``requests`` client.
# ---------------------------------------------------------------------------


class _FixtureHandler(BaseHTTPRequestHandler):
    """Serve ORCID-like ``/v3.0/{iD}/record`` responses from fixture JSON.

    The handler is parameterised at server-construction time via
    ``server.fixture_map`` (path -> (status, json_path_or_text)).
    """

    def do_GET(self) -> None:  # noqa: N802 (stdlib API)
        server: _FixtureServer = self.server  # type: ignore[assignment]
        spec = server.fixture_map.get(self.path)
        if spec is None:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "fixture not registered"}')
            return
        status, payload = spec
        if isinstance(payload, Path):
            body = payload.read_bytes()
            content_type = "application/json"
        elif isinstance(payload, (bytes, bytearray)):
            body = bytes(payload)
            content_type = "application/octet-stream"
        else:
            body = payload.encode("utf-8")
            content_type = "text/plain"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Silence stderr access-log noise during tests.
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


class _FixtureServer(ThreadingHTTPServer):
    fixture_map: dict[str, tuple[int, object]]


@pytest.fixture
def orcid_fixture_server() -> (
    Iterator[Callable[[dict[str, tuple[int, object]]], str]]
):
    """Spin up a local HTTP server on an ephemeral port; yield a base_url builder.

    Usage::

        def test_something(orcid_fixture_server):
            base = orcid_fixture_server({
                "/v3.0/0000-0002-1825-0097/record": (
                    200,
                    FIXTURE_DIR / "orcid_0000-0002-1825-0097_record.json",
                ),
            })
            rec = verify_orcid("0000-0002-1825-0097", base_url=base)
    """
    server = _FixtureServer(("127.0.0.1", 0), _FixtureHandler)
    server.fixture_map = {}
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def configure(fixture_map: dict[str, tuple[int, object]]) -> str:
        server.fixture_map = fixture_map
        return f"http://127.0.0.1:{port}/v3.0"

    try:
        yield configure
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


# ---------------------------------------------------------------------------
# normalize_orcid — pure unit, no HTTP at all.
# ---------------------------------------------------------------------------


class TestNormalizeOrcid:
    def test_accepts_bare_form(self) -> None:
        assert normalize_orcid("0000-0002-1825-0097") == "0000-0002-1825-0097"

    def test_accepts_orcid_org_url(self) -> None:
        assert (
            normalize_orcid("https://orcid.org/0000-0002-1825-0097")
            == "0000-0002-1825-0097"
        )

    def test_accepts_sandbox_url(self) -> None:
        assert (
            normalize_orcid("https://sandbox.orcid.org/0000-0002-1825-0097")
            == "0000-0002-1825-0097"
        )

    def test_accepts_trailing_slash(self) -> None:
        assert (
            normalize_orcid("https://orcid.org/0000-0002-1825-0097/")
            == "0000-0002-1825-0097"
        )

    def test_accepts_x_check_digit(self) -> None:
        # 0000-0002-1825-009X is checksum-invalid for body 0000000218250 09;
        # use a known X-tail iD: 0000-0001-5109-3700 -> body checksum '0',
        # for an X-tail we need a contrived but valid one.
        # Use 0000-0002-1694-233X (a real public ORCID iD with X check).
        assert (
            normalize_orcid("0000-0002-1694-233X") == "0000-0002-1694-233X"
        )

    def test_rejects_garbage(self) -> None:
        with pytest.raises(GateFailure) as ei:
            normalize_orcid("not-an-orcid")
        assert ei.value.check == "orcid"
        assert "canonical" in ei.value.reason

    def test_rejects_bad_checksum(self) -> None:
        # Last digit deliberately wrong.
        with pytest.raises(GateFailure) as ei:
            normalize_orcid("0000-0002-1825-0098")
        assert ei.value.check == "orcid"
        assert "checksum" in ei.value.reason


# ---------------------------------------------------------------------------
# verify_orcid — real HTTP against the local fixture server.
# ---------------------------------------------------------------------------


class TestVerifyOrcidAgainstFixtureServer:
    def test_full_name_record(self, orcid_fixture_server) -> None:
        base = orcid_fixture_server(
            {
                "/v3.0/0000-0002-1825-0097/record": (
                    200,
                    FIXTURE_DIR / "orcid_0000-0002-1825-0097_record.json",
                ),
            }
        )
        rec = verify_orcid("0000-0002-1825-0097", base_url=base)
        assert isinstance(rec, OrcidRecord)
        assert rec.orcid_id == "0000-0002-1825-0097"
        assert rec.given_name == "Josiah"
        assert rec.family_name == "Carberry"
        assert rec.credit_name == "Josiah S. Carberry"
        assert rec.display_name == "Josiah S. Carberry"

    def test_minimal_name_record_falls_back_to_family_only(
        self, orcid_fixture_server
    ) -> None:
        base = orcid_fixture_server(
            {
                "/v3.0/0000-0001-2345-6789/record": (
                    200,
                    FIXTURE_DIR / "orcid_0000-0001-2345-6789_record_minimal.json",
                ),
            }
        )
        rec = verify_orcid("0000-0001-2345-6789", base_url=base)
        assert rec.given_name is None
        assert rec.family_name == "Solo"
        assert rec.credit_name is None
        assert rec.display_name == "Solo"

    def test_404_raises_does_not_resolve(self, orcid_fixture_server) -> None:
        base = orcid_fixture_server({})  # nothing registered -> 404
        with pytest.raises(GateFailure) as ei:
            verify_orcid("0000-0002-1825-0097", base_url=base)
        assert ei.value.check == "orcid"
        assert "does not resolve" in ei.value.reason
        assert "HTTP 404" in ei.value.detail

    def test_500_raises_non_success(self, orcid_fixture_server) -> None:
        base = orcid_fixture_server(
            {
                "/v3.0/0000-0002-1825-0097/record": (500, "boom"),
            }
        )
        with pytest.raises(GateFailure) as ei:
            verify_orcid("0000-0002-1825-0097", base_url=base)
        assert "non-success" in ei.value.reason
        assert "HTTP 500" in ei.value.detail

    def test_non_json_body_raises(self, orcid_fixture_server) -> None:
        base = orcid_fixture_server(
            {
                "/v3.0/0000-0002-1825-0097/record": (
                    200,
                    b"<html>nope</html>",
                ),
            }
        )
        with pytest.raises(GateFailure) as ei:
            verify_orcid("0000-0002-1825-0097", base_url=base)
        assert "non-json" in ei.value.reason

    def test_unfamiliar_record_shape_raises(self, orcid_fixture_server) -> None:
        base = orcid_fixture_server(
            {
                "/v3.0/0000-0002-1825-0097/record": (
                    200,
                    FIXTURE_DIR / "orcid_0000-0002-1825-0097_record_garbled.json",
                ),
            }
        )
        with pytest.raises(GateFailure) as ei:
            verify_orcid("0000-0002-1825-0097", base_url=base)
        assert "unfamiliar" in ei.value.reason

    def test_network_unreachable_raises_loudly(self) -> None:
        # Use a closed port to surface a real connect-failure path.
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            closed_port = s.getsockname()[1]
        # Socket closed when block exits -> port now unreachable.
        with pytest.raises(GateFailure) as ei:
            verify_orcid(
                "0000-0002-1825-0097",
                base_url=f"http://127.0.0.1:{closed_port}/v3.0",
            )
        assert ei.value.check == "orcid"
        assert "unreachable" in ei.value.reason


# ---------------------------------------------------------------------------
# Optional real-network test against pub.orcid.org.
# ---------------------------------------------------------------------------


@pytest.mark.network
@pytest.mark.skipif(
    os.environ.get("SCITEX_RUN_NETWORK_TESTS") != "1",
    reason="opt in by setting SCITEX_RUN_NETWORK_TESTS=1",
)
def test_real_orcid_org_resolves() -> None:
    rec = verify_orcid("0000-0002-1825-0097")  # Josiah Carberry
    assert rec.orcid_id == "0000-0002-1825-0097"
    # Don't pin the name shape — ORCID may revise display name fields.
    assert rec.display_name
