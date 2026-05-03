# pykonf — Agent Guide

## Run the API

```sh
SECRET_KEY=secret READ_KEY=read DATA_FEATUREFLAGS_PAYMENT=value python api.py
```

Or after `pip install -e .`:

```sh
SECRET_KEY=secret READ_KEY=read DATA_FEATUREFLAGS_PAYMENT=value pykonf
```

Required env vars: `SECRET_KEY` and `READ_KEY` (checked at import time, absent raises).

Config is seeded from `DATA_*` env vars at startup (underscore-separated keys → nested dict), then persisted to `CONFIG_FILE` (default `config.json`).

## REST API Endpoints

Read endpoints (`GET`) require a `read_key` header matching `READ_KEY`. Mutation endpoints (`PUT`, `POST`, `DELETE`) require a `secret_key` header matching `SECRET_KEY` and are rate-limited to 1/minute (shared across all mutations).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | — | Health check |
| `GET` | `/config` | `read_key` | Returns full config (Cache-Control: max-age=60) |
| `GET` | `/config/{path}` | `read_key` | Read nested value (e.g. `/config/featureflags/payment`) |
| `PUT` | `/config` | `secret_key` | Deep-merge partial update |
| `POST` | `/config/{path}` | `secret_key` | Set value at path. Body: `{"value": any}` or raw JSON |
| `DELETE` | `/config/{path}` | `secret_key` | Remove key at path |

## MCP Tools

The MCP server runs on the same process at `/mcp` (Streamable HTTP transport). Connect from Claude Code, VS Code, or any MCP client.

| Tool | Parameters | Description |
|------|-----------|-------------|
| `read_config` | `read_key`, `path` (optional) | Read full config or subtree at slash-separated path |
| `list_keys` | `read_key`, `path` (optional) | List keys under a path |
| `set_value` | `path`, `value`, `secret_key` | Set value at path |
| `delete_key` | `path`, `secret_key` | Delete key at path |

### Claude Code MCP configuration

```json
{
  "mcpServers": {
    "pykonf": {
      "transport": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Or via CLI:

```sh
claude mcp add --transport http pykonf http://localhost:8000/mcp
```

## JS Client Reference App

A reference implementation at `js-client/` shows how a JS frontend reads config via the REST API. It's **not** part of the Python package (excluded by `pyproject.toml`'s `packages.find.where = ["src"]`). No build tools needed — open `index.html` directly.

## Tests

```sh
bash test_api.sh
# or directly:
python -m pytest tests/ -v
```

## Commands

```sh
# format
black src/pykonf/
```
