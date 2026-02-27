"""Test configuration for Flatfish."""

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
            "source": "test/dataset",
            "splits": ["train"],
            "image_column": "image",
        },
        "processing": {
            "extract_entities": True,
            "entity_context": True,
        },
        "summary": {
            "enabled": True,
            "model": "qwen-turbo",
        },
        "output": {
            "transcriptions_dir": "transcriptions",
            "entities_dir": "entities",
            "summaries_dir": "summaries",
            "site_dir": "_site",
        },
        "website": {
            "title": "Test Collection",
            "password": "test123",
        },
    }
