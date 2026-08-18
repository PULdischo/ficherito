"""Test configuration for Ficherito."""

import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "dataset": {
            "images_dir": "images",
            "recursive": False,
        },
        "processing": {
            "extract_entities": True,
            "entity_context": True,
        },
        "output": {
            "transcriptions_dir": "transcriptions",
            "entities_dir": "entities",
            "eleventy_dir": "site",
            "site_dir": "site/_site",
        },
        "website": {
            "title": "Test Collection",
            "password": "test123",
        },
    }
