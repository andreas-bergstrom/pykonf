import json
from pykonf import config as cfg


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_read_config_empty(client):
    resp = client.get("/config")
    assert resp.status_code == 200
    assert resp.json() == {}


def test_read_config_with_data(client):
    cfg.json_data = {"db": {"host": "localhost", "port": 5432}, "feature": "enabled"}
    resp = client.get("/config")
    assert resp.status_code == 200
    assert resp.json() == {"db": {"host": "localhost", "port": 5432}, "feature": "enabled"}


def test_read_config_cache_control(client):
    resp = client.get("/config")
    assert resp.headers.get("cache-control") == "max-age=60"


def test_read_config_path_nested(client):
    cfg.json_data = {"featureflags": {"payment": "enabled"}}
    resp = client.get("/config/featureflags/payment")
    assert resp.status_code == 200
    assert resp.json() == "enabled"


def test_read_config_path_single(client):
    cfg.json_data = {"host": "localhost"}
    resp = client.get("/config/host")
    assert resp.status_code == 200
    assert resp.json() == "localhost"


def test_read_config_path_404(client):
    resp = client.get("/config/nonexistent")
    assert resp.status_code == 404


def test_read_config_path_deep_404(client):
    cfg.json_data = {"a": {"b": 1}}
    resp = client.get("/config/a/x")
    assert resp.status_code == 404


def test_put_config_no_auth(client):
    resp = client.put("/config", json={"key": "value"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Unauthorized"}


def test_put_config_unauthorized_wrong_key(client):
    resp = client.put("/config", json={"key": "value"}, headers={"secret-key": "wrong"})
    assert resp.status_code == 401


def test_put_config_merge(client, auth_headers):
    cfg.json_data = {"existing": 1}
    resp = client.put("/config", json={"new": 2}, headers=auth_headers)
    assert resp.status_code == 200
    assert cfg.json_data == {"existing": 1, "new": 2}


def test_put_config_deep_merge(client, auth_headers):
    cfg.json_data = {"db": {"host": "localhost", "port": 5432}}
    resp = client.put("/config", json={"db": {"port": 9999, "user": "admin"}}, headers=auth_headers)
    assert resp.status_code == 200
    assert cfg.json_data == {"db": {"host": "localhost", "port": 9999, "user": "admin"}}


def test_post_config_path(client, auth_headers):
    resp = client.post("/config/theme/color", json={"value": "dark"}, headers=auth_headers)
    assert resp.status_code == 200
    assert cfg.json_data == {"theme": {"color": "dark"}}


def test_post_config_path_raw_value(client, auth_headers):
    resp = client.post("/config/raw", json="rawstring", headers=auth_headers)
    assert resp.status_code == 200
    assert cfg.json_data == {"raw": "rawstring"}


def test_post_config_path_raw_number(client, auth_headers):
    resp = client.post("/config/count", json=42, headers=auth_headers)
    assert resp.status_code == 200
    assert cfg.json_data == {"count": 42}


def test_post_config_path_no_auth(client):
    resp = client.post("/config/key", json={"value": "x"})
    assert resp.status_code == 401


def test_post_config_path_overwrite(client, auth_headers):
    cfg.json_data = {"theme": {"color": "light"}}
    resp = client.post("/config/theme/color", json={"value": "dark"}, headers=auth_headers)
    assert resp.status_code == 200
    assert cfg.json_data == {"theme": {"color": "dark"}}


def test_delete_config_path(client, auth_headers):
    cfg.json_data = {"a": {"b": 1, "c": 2}}
    resp = client.delete("/config/a/b", headers=auth_headers)
    assert resp.status_code == 200
    assert cfg.json_data == {"a": {"c": 2}}


def test_delete_config_path_404(client, auth_headers):
    resp = client.delete("/config/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_config_path_no_auth(client):
    resp = client.delete("/config/key")
    assert resp.status_code == 401


def test_rate_limit_429(monkeypatch, client, auth_headers):
    monkeypatch.setattr(cfg, "DISABLE_RATE_LIMIT", False)
    monkeypatch.setattr(cfg, "MUTATION_COOLDOWN", 9999)
    cfg._last_mutation_time = 0.0
    client.put("/config", json={"a": 1}, headers=auth_headers)
    resp = client.put("/config", json={"b": 2}, headers=auth_headers)
    assert resp.status_code == 429


def test_put_config_invalid_body(client, auth_headers):
    resp = client.put("/config", content=b"not-json", headers=auth_headers)
    assert resp.status_code == 422


def test_read_config_path_preserves_types(client):
    cfg.json_data = {"num": 42, "flag": True, "items": [1, 2, 3]}
    assert client.get("/config/num").json() == 42
    assert client.get("/config/flag").json() is True
    assert client.get("/config/items").json() == [1, 2, 3]
