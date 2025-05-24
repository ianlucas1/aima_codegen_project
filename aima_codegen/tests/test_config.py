import os
import stat
import tempfile
import shutil
import json
import configparser
import pytest
from pathlib import Path
from aima_codegen.config import ConfigManager, DEFAULT_CONFIG, DEFAULT_MODEL_COSTS

@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    # Patch HOME to tmp_path
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".AIMA_CodeGen"
    config_dir.mkdir()
    yield config_dir

@pytest.fixture
def config_manager(temp_config_dir, monkeypatch):
    # Patch Path.home() to tmp_path
    monkeypatch.setattr("pathlib.Path.home", lambda: temp_config_dir.parent)
    return ConfigManager()

def test_default_config_created(config_manager):
    assert config_manager.config_path.exists()
    content = config_manager.config_path.read_text()
    assert "[General]" in content
    # Permissions should be 0o600
    mode = os.stat(config_manager.config_path).st_mode
    assert stat.S_IMODE(mode) == 0o600

def test_default_model_costs_created(config_manager):
    assert config_manager.model_costs_path.exists()
    with open(config_manager.model_costs_path) as f:
        data = json.load(f)
    assert "gpt-4.1-2025-04-14" in data
    assert isinstance(data["gpt-4.1-2025-04-14"], dict)

def test_get_existing_value(config_manager):
    val = config_manager.get("General", "default_provider")
    assert val == "OpenAI"

def test_get_boolean_value(config_manager):
    val = config_manager.get("General", "redact_llm_logs")
    assert val is True

def test_get_numeric_value(config_manager):
    val = config_manager.get("LLM", "codegen_temperature")
    assert isinstance(val, float)
    assert val == 0.2
    val2 = config_manager.get("LLM", "codegen_max_tokens")
    assert isinstance(val2, int)
    assert val2 == 4000

def test_get_missing_value_returns_fallback(config_manager):
    val = config_manager.get("General", "does_not_exist", fallback="fallback")
    assert val == "fallback"
    val2 = config_manager.get("NoSection", "no_key", fallback=123)
    assert val2 == 123

def test_set_and_get_value(config_manager):
    config_manager.set("General", "test_key", "test_value")
    val = config_manager.get("General", "test_key")
    assert val == "test_value"
    # Permissions should remain 0o600
    mode = os.stat(config_manager.config_path).st_mode
    assert stat.S_IMODE(mode) == 0o600

def test_set_creates_section_if_missing(config_manager):
    config_manager.set("NewSection", "foo", "bar")
    val = config_manager.get("NewSection", "foo")
    assert val == "bar"

def test_get_model_costs_valid(config_manager):
    costs = config_manager.get_model_costs()
    assert isinstance(costs, dict)
    assert "gpt-4.1-2025-04-14" in costs
    assert "prompt_cost_per_1k_tokens" in costs["gpt-4.1-2025-04-14"]

def test_get_model_costs_invalid(tmp_path, monkeypatch):
    # Patch HOME to tmp_path
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".AIMA_CodeGen"
    config_dir.mkdir()
    # Write invalid JSON
    model_costs_path = config_dir / "model_costs.json"
    model_costs_path.write_text("not a json")
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    cm = ConfigManager()
    cm.model_costs_path = model_costs_path
    with pytest.raises(RuntimeError) as e:
        cm.get_model_costs()
    assert "invalid data" in str(e.value)

def test_expand_path(config_manager):
    p = config_manager.expand_path("~/.AIMA_CodeGen/config.ini")
    assert str(p).startswith(str(Path.home()))
