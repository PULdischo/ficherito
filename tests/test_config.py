"""Tests for configuration module."""

import pytest
import yaml
from pathlib import Path

from flatfish.config import (
    FlatfishConfig,
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
    config_path = temp_dir / "flatfish.yaml"
    
    with open(config_path, "w") as f:
        yaml.dump(sample_config, f)
    
    config = load_config(config_path)
    
    assert config.dataset.source == "test/dataset"
    assert config.dataset.splits == ["train"]
    assert config.website.title == "Test Collection"


def test_load_config_missing_file():
    """Test error when config file is missing."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("nonexistent.yaml"))


def test_config_validation(temp_dir):
    """Test that invalid config raises error."""
    config_path = temp_dir / "flatfish.yaml"
    
    # Missing required field
    with open(config_path, "w") as f:
        yaml.dump({"processing": {}}, f)
    
    with pytest.raises(Exception):  # Pydantic validation error
        load_config(config_path)


def test_load_env(temp_dir, monkeypatch):
    """Test loading environment variables."""
    # Create .env file
    env_path = temp_dir / ".env"
    with open(env_path, "w") as f:
        f.write("HUGGINGFACE_TOKEN=hf_test123\n")
        f.write("DASHSCOPE_API_KEY=sk_test456\n")
    
    # Change to temp dir so .env is found
    monkeypatch.chdir(temp_dir)
    
    env = load_env()
    
    assert env.huggingface_token == "hf_test123"
    assert env.dashscope_api_key == "sk_test456"
