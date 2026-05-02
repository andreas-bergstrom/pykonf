import json
import os
import pytest
from pykonf import config as cfg


def test_load_config_no_file(monkeypatch):
    monkeypatch.setattr(cfg, "CONFIG_FILE", "/nonexistent/does_not_exist.json")
    result = cfg.load_config()
    assert result == {}


def test_load_config_with_file(config_file):
    result = cfg.load_config()
    assert result == {"host": "localhost", "port": 8080}


def test_load_config_data_env(monkeypatch):
    monkeypatch.setattr(cfg, "CONFIG_FILE", "/nonexistent/nope.json")
    monkeypatch.setenv("DATA_FEATUREFLAGS_PAYMENT", "enabled")
    monkeypatch.setenv("DATA_DATABASE_HOST", "prod")
    result = cfg.load_config()
    assert result == {"featureflags": {"payment": "enabled"}, "database": {"host": "prod"}}


def test_save_config(tmp_path):
    path = tmp_path / "test.json"
    cfg.save_config({"key": "value", "nested": {"a": 1}})
    with open(cfg.CONFIG_FILE) as f:
        data = json.load(f)
    assert data == {"key": "value", "nested": {"a": 1}}
    os.unlink(cfg.CONFIG_FILE)


def test_deep_merge_empty_base():
    base = {}
    cfg.deep_merge(base, {"a": 1, "b": 2})
    assert base == {"a": 1, "b": 2}


def test_deep_merge_nested():
    base = {"a": {"x": 1}}
    cfg.deep_merge(base, {"a": {"y": 2}})
    assert base == {"a": {"x": 1, "y": 2}}


def test_deep_merge_overwrite():
    base = {"a": 1}
    cfg.deep_merge(base, {"a": 2})
    assert base == {"a": 2}


def test_deep_merge_deep_nesting():
    base = {"db": {"host": "localhost", "port": 5432}}
    cfg.deep_merge(base, {"db": {"port": 9999, "user": "admin"}})
    assert base == {"db": {"host": "localhost", "port": 9999, "user": "admin"}}


def test_get_at_path_root():
    config = {"a": 1}
    assert cfg.get_at_path(config, "") == config


def test_get_at_path_single():
    config = {"a": 1, "b": 2}
    assert cfg.get_at_path(config, "a") == 1


def test_get_at_path_nested():
    config = {"a": {"b": {"c": 42}}}
    assert cfg.get_at_path(config, "a/b/c") == 42


def test_get_at_path_leading_slash():
    config = {"a": {"b": 1}}
    assert cfg.get_at_path(config, "/a/b") == 1


def test_get_at_path_missing():
    with pytest.raises(KeyError):
        cfg.get_at_path({"a": 1}, "b")


def test_get_at_path_missing_nested():
    with pytest.raises(KeyError):
        cfg.get_at_path({"a": {"b": 1}}, "a/x")


def test_set_at_path_new():
    config = {}
    cfg.set_at_path(config, "key", "value")
    assert config == {"key": "value"}


def test_set_at_path_nested():
    config = {}
    cfg.set_at_path(config, "a/b/c", 42)
    assert config == {"a": {"b": {"c": 42}}}


def test_set_at_path_overwrite():
    config = {"a": 1}
    cfg.set_at_path(config, "a", 2)
    assert config["a"] == 2


def test_set_at_path_nested_overwrite():
    config = {"a": {"b": 1}}
    cfg.set_at_path(config, "a/b", 2)
    assert config["a"] == {"b": 2}


def test_set_at_path_root_raises():
    with pytest.raises(ValueError, match="Cannot set root"):
        cfg.set_at_path({}, "", "x")


def test_set_at_path_into_scalar_raises():
    config = {"a": 1}
    with pytest.raises(ValueError, match="Cannot traverse into non-dict"):
        cfg.set_at_path(config, "a/b", 2)


def test_delete_at_path():
    config = {"a": {"b": 1, "c": 2}}
    cfg.delete_at_path(config, "a/b")
    assert config == {"a": {"c": 2}}


def test_delete_at_path_root_raises():
    with pytest.raises(ValueError, match="Cannot delete root"):
        cfg.delete_at_path({"a": 1}, "")


def test_delete_at_path_missing():
    with pytest.raises(KeyError):
        cfg.delete_at_path({"a": 1}, "b")


def test_delete_at_path_missing_nested():
    with pytest.raises(KeyError):
        cfg.delete_at_path({"a": {"b": 1}}, "a/x")


def test_check_mutation_rate_disabled():
    cfg.DISABLE_RATE_LIMIT = True
    cfg.check_mutation_rate()
    cfg.check_mutation_rate()
    assert True


def test_check_mutation_rate_blocks(monkeypatch):
    cfg.DISABLE_RATE_LIMIT = False
    cfg._last_mutation_time = 0.0
    monkeypatch.setattr(cfg, "MUTATION_COOLDOWN", 9999)
    cfg.check_mutation_rate()
    with pytest.raises(RuntimeError, match="rate limit"):
        cfg.check_mutation_rate()
