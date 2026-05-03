import json
from typing import Any
from fastmcp import FastMCP

from pykonf import config as cfg

mcp_server = FastMCP("pykonf")


@mcp_server.tool()
def read_config(read_key: str, path: str | None = None) -> str:
    """Read the current configuration. Optionally provide a path (e.g. 'featureflags/payment') to read a subtree. Requires read_key for authorization."""
    if read_key != cfg.READ_KEY:
        return "Error: Unauthorized"
    try:
        if path:
            value = cfg.get_at_path(cfg.json_data, path)
        else:
            value = cfg.json_data
        return json.dumps(value, indent=2, ensure_ascii=False)
    except KeyError as e:
        return f"Error: {e}"


@mcp_server.tool()
def list_keys(read_key: str, path: str | None = None) -> str:
    """List the keys at the given path (or root). Requires read_key for authorization."""
    if read_key != cfg.READ_KEY:
        return "Error: Unauthorized"
    try:
        if path:
            target = cfg.get_at_path(cfg.json_data, path)
        else:
            target = cfg.json_data
        if isinstance(target, dict):
            keys = list(target.keys())
            return "\n".join(keys) if keys else "(empty)"
        else:
            return f"Value at '{path}' is not a dict (type: {type(target).__name__})"
    except KeyError as e:
        return f"Error: {e}"


@mcp_server.tool()
def set_value(path: str, value: Any, secret_key: str) -> str:
    """Set a value at the given path (e.g. 'featureflags/payment'). Requires secret_key for authorization."""
    if secret_key != cfg.SECRET_KEY:
        return "Error: Unauthorized"

    try:
        cfg.check_mutation_rate()
        cfg.set_at_path(cfg.json_data, path, value)
        cfg.save_config(cfg.json_data)
        return f"Set {path} = {json.dumps(value, ensure_ascii=False)}"
    except RuntimeError as e:
        return f"Error: {e}"
    except (ValueError, KeyError) as e:
        return f"Error: {e}"


@mcp_server.tool()
def delete_key(path: str, secret_key: str) -> str:
    """Delete a key at the given path. Requires secret_key for authorization."""
    if secret_key != cfg.SECRET_KEY:
        return "Error: Unauthorized"

    try:
        cfg.check_mutation_rate()
        cfg.delete_at_path(cfg.json_data, path)
        cfg.save_config(cfg.json_data)
        return f"Deleted {path}"
    except RuntimeError as e:
        return f"Error: {e}"
    except KeyError as e:
        return f"Error: {e}"
