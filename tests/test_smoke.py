"""Smoke tests — verify the package exposes a usable version string."""

import scitex_agentic_journal


def test_package_version_attribute_is_a_string():
    # Arrange
    pkg = scitex_agentic_journal
    # Act
    version = pkg.__version__
    # Assert
    assert isinstance(version, str)


def test_package_version_attribute_is_non_empty():
    # Arrange
    pkg = scitex_agentic_journal
    # Act
    version = pkg.__version__
    # Assert
    assert version
