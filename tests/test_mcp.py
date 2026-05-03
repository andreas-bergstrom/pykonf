import json
import pytest
from pykonf import config as cfg


def _mcp_headers(session_id=None):
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session_id:
        h["mcp-session-id"] = session_id
    return h


def _init_session(client):
    resp = client.post(
        "/mcp",
        headers=_mcp_headers(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"},
            },
        },
    )
    assert resp.status_code == 200
    sid = resp.headers.get("mcp-session-id")
    resp = client.post(
        "/mcp",
        headers=_mcp_headers(sid),
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )
    assert resp.status_code in (200, 202)
    return sid


def _call_tool(client, session_id, name, arguments=None):
    resp = client.post(
        "/mcp",
        headers=_mcp_headers(session_id),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        },
    )
    assert resp.status_code == 200, f"tool call failed: {resp.status_code} {resp.text[:300]}"
    events = [line for line in resp.text.split("\n") if line.startswith("data: ")]
    assert events, f"no SSE data events in response: {resp.text[:300]}"
    return json.loads(events[-1].replace("data: ", "", 1))


def _list_tools(client, session_id):
    resp = client.post(
        "/mcp",
        headers=_mcp_headers(session_id),
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    assert resp.status_code == 200
    events = [line for line in resp.text.split("\n") if line.startswith("data: ")]
    assert events
    return json.loads(events[-1].replace("data: ", "", 1))


class TestMCPSession:
    def test_initialize(self, client):
        sid = _init_session(client)
        assert sid, "no mcp-session-id header"

    def test_list_tools(self, client):
        sid = _init_session(client)
        data = _list_tools(client, sid)
        tool_names = [t["name"] for t in data["result"]["tools"]]
        assert "read_config" in tool_names
        assert "set_value" in tool_names
        assert "delete_key" in tool_names
        assert "list_keys" in tool_names

    def test_read_config_unauthorized(self, client):
        cfg.json_data = {"secret": "value"}
        sid = _init_session(client)
        data = _call_tool(client, sid, "read_config", {"read_key": "wrong", "path": None})
        assert "Unauthorized" in data["result"]["content"][0]["text"]

    def test_read_config_empty(self, client):
        sid = _init_session(client)
        data = _call_tool(client, sid, "read_config", {"read_key": "test-read-key"})
        text = data["result"]["content"][0]["text"]
        assert json.loads(text) == {}

    def test_read_config_with_data(self, client):
        cfg.json_data = {"db": {"host": "localhost"}, "port": 8080}
        sid = _init_session(client)
        data = _call_tool(client, sid, "read_config", {"read_key": "test-read-key"})
        text = data["result"]["content"][0]["text"]
        assert json.loads(text) == {"db": {"host": "localhost"}, "port": 8080}

    def test_read_config_path(self, client):
        cfg.json_data = {"featureflags": {"payment": "enabled", "debug": False}}
        sid = _init_session(client)
        data = _call_tool(client, sid, "read_config", {"read_key": "test-read-key", "path": "featureflags/payment"})
        text = data["result"]["content"][0]["text"]
        assert json.loads(text) == "enabled"

    def test_read_config_path_not_found(self, client):
        cfg.json_data = {"a": 1}
        sid = _init_session(client)
        data = _call_tool(client, sid, "read_config", {"read_key": "test-read-key", "path": "a/x"})
        assert "Error" in data["result"]["content"][0]["text"]

    def test_list_keys_unauthorized(self, client):
        sid = _init_session(client)
        data = _call_tool(client, sid, "list_keys", {"read_key": "wrong"})
        assert "Unauthorized" in data["result"]["content"][0]["text"]

    def test_list_keys_root(self, client):
        cfg.json_data = {"a": 1, "b": {"c": 2}}
        sid = _init_session(client)
        data = _call_tool(client, sid, "list_keys", {"read_key": "test-read-key"})
        keys = data["result"]["content"][0]["text"].split("\n")
        assert "a" in keys
        assert "b" in keys

    def test_list_keys_nested(self, client):
        cfg.json_data = {"a": {"b": 1, "c": 2}}
        sid = _init_session(client)
        data = _call_tool(client, sid, "list_keys", {"read_key": "test-read-key", "path": "a"})
        keys = data["result"]["content"][0]["text"].split("\n")
        assert "b" in keys
        assert "c" in keys

    def test_list_keys_on_scalar(self, client):
        cfg.json_data = {"a": 42}
        sid = _init_session(client)
        data = _call_tool(client, sid, "list_keys", {"read_key": "test-read-key", "path": "a"})
        assert "not a dict" in data["result"]["content"][0]["text"]

    def test_set_value(self, client):
        sid = _init_session(client)
        data = _call_tool(
            client, sid, "set_value",
            {"path": "theme/color", "value": "dark", "secret_key": "test-secret-key"},
        )
        assert "Set" in data["result"]["content"][0]["text"]
        assert cfg.json_data == {"theme": {"color": "dark"}}

    def test_set_value_unauthorized(self, client):
        sid = _init_session(client)
        data = _call_tool(client, sid, "set_value", {"path": "x", "value": 1, "secret_key": "wrong"})
        assert "Unauthorized" in data["result"]["content"][0]["text"]
        assert cfg.json_data == {}

    def test_set_value_nested(self, client):
        cfg.json_data = {"existing": True}
        sid = _init_session(client)
        data = _call_tool(
            client, sid, "set_value",
            {"path": "a/b/c", "value": 42, "secret_key": "test-secret-key"},
        )
        assert "Set" in data["result"]["content"][0]["text"]
        assert cfg.json_data == {"existing": True, "a": {"b": {"c": 42}}}

    def test_delete_key(self, client):
        cfg.json_data = {"a": {"b": 1, "c": 2}}
        sid = _init_session(client)
        data = _call_tool(client, sid, "delete_key", {"path": "a/b", "secret_key": "test-secret-key"})
        assert "Deleted" in data["result"]["content"][0]["text"]
        assert cfg.json_data == {"a": {"c": 2}}

    def test_delete_key_not_found(self, client):
        sid = _init_session(client)
        data = _call_tool(client, sid, "delete_key", {"path": "nonexistent", "secret_key": "test-secret-key"})
        assert "Error" in data["result"]["content"][0]["text"]

    def test_delete_key_unauthorized(self, client):
        cfg.json_data = {"x": 1}
        sid = _init_session(client)
        data = _call_tool(client, sid, "delete_key", {"path": "x", "secret_key": "wrong"})
        assert "Unauthorized" in data["result"]["content"][0]["text"]
        assert cfg.json_data == {"x": 1}
