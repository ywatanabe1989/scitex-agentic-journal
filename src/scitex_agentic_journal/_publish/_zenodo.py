"""Zenodo + Zenodo-Sandbox id-minter stubs.

Both stubs raise :class:`NotImplementedError` from :meth:`mint` —
explicitly, with guidance, so the next maintainer knows what to wire
up. They are *not* silent fallbacks to ``InternalIdMinter``.
"""

from __future__ import annotations

from scitex_agentic_journal._publish._types import (
    Backend,
    IdMinter,
    MintInput,
    PersistentId,
)


class ZenodoStub:
    """Production Zenodo backend — to be wired with real DOI minting.

    Will use the Zenodo REST API + a SciTeX-owned API token. Mints a
    real :rfc:`8615`-compliant DOI under the SciTeX namespace.
    """

    backend: Backend = "zenodo"

    def mint(self, mint_input: MintInput) -> PersistentId:
        raise NotImplementedError(
            "ZenodoStub.mint() is a deliberate placeholder. "
            "Wire it to https://developers.zenodo.org/#deposit-actions "
            "and supply a token via SCITEX_AJ_ZENODO_TOKEN before use. "
            "No silent fallback to the internal minter."
        )


class ZenodoSandboxStub:
    """Zenodo-Sandbox backend — same shape, sandbox API host.

    Used in CI / staging to exercise the publish pipeline against a
    real DOI registry without burning real DOIs.
    """

    backend: Backend = "zenodo-sandbox"

    def mint(self, mint_input: MintInput) -> PersistentId:
        raise NotImplementedError(
            "ZenodoSandboxStub.mint() is a deliberate placeholder. "
            "Wire it to https://sandbox.zenodo.org/api/ and supply a token "
            "via SCITEX_AJ_ZENODO_SANDBOX_TOKEN before use."
        )


# Confirm the stubs satisfy the IdMinter Protocol shape at import time.
_check_zenodo: IdMinter = ZenodoStub()
_check_zenodo_sandbox: IdMinter = ZenodoSandboxStub()
del _check_zenodo, _check_zenodo_sandbox
