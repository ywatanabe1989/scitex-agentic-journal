"""End-to-end pipeline integration tests.

These tests drive the public CLI (and a thin slice of the public Python
API for the M4 mint step, which has no CLI verb) against a real
on-disk ``$SCITEX_AGENTIC_JOURNAL_HOME`` so the cross-stage on-disk
contract is exercised — not just each stage in isolation.
"""
