"""Tests for configuration module."""

import pytest
import yaml
from pathlib import Path

from ficherito.config import (
    FicheritoConfig,
    load_config,
    load_env,
    get_default_config,
)


def test_default_config():
    """Test that default config is valid."""
    config = get_default_config()
    
    assert "dataset" in config
    assert "processing" in config
    assert "output" in config
    assert "website" in config


def test_load_config(temp_dir, sample_config):
    """Test loading config from file."""
    config_path = temp_dir / "ficherito.yaml"
    
    with open(config_path, "w") as f:
        yaml.dump(sample_config, f)
    
    config = load_config(config_path)
    
    assert config.dataset.images_dir == "images"
    assert config.dataset.recursive is False
    assert config.website.title == "Test Collection"


def test_load_config_missing_file():
    """Test error when config file is missing."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("nonexistent.yaml"))


def test_config_validation(temp_dir):
    """Test that invalid config raises error."""
    config_path = temp_dir / "ficherito.yaml"
    
    # Missing required field
    with open(config_path, "w") as f:
        yaml.dump({"processing": {}}, f)
    
    with pytest.raises(Exception):  # Pydantic validation error
        load_config(config_path)


@pytest.mark.parametrize(
    "website_yaml",
    [
        {},  # password key missing entirely
        {"password": None},  # explicit null
        {"password": ""},  # explicit empty string
    ],
)
def test_password_unset_disables_gate(temp_dir, website_yaml):
    """Missing/null/empty password should resolve to a falsy value so the
    site templates skip the password gate (see WebsiteConfig.password)."""
    config_path = temp_dir / "ficherito.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"dataset": {"images_dir": "images"}, "website": website_yaml}, f)

    config = load_config(config_path)

    assert not config.website.password


def test_password_set_is_kept(temp_dir):
    config_path = temp_dir / "ficherito.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"dataset": {"images_dir": "images"}, "website": {"password": "secret"}}, f)

    config = load_config(config_path)

    assert config.website.password == "secret"


def test_load_env(temp_dir, monkeypatch):
    """Test loading environment variables."""
    # Create .env file
    env_path = temp_dir / ".env"
    with open(env_path, "w") as f:
        f.write("OPENAI_BASE_URL=https://example.com/v1\n")
        f.write("OPENAI_API_KEY=sk_test456\n")
        f.write("OPENAI_MODEL=qwen-vl-max\n")
    
    # Change to temp dir so .env is found
    monkeypatch.chdir(temp_dir)
    
    env = load_env()
    
    assert env.api_base_url == "https://example.com/v1"
    assert env.api_key == "sk_test456"
    assert env.api_model == "qwen-vl-max"
