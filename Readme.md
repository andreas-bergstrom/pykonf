# pykonf

Simple HTTP API + MCP server to manage client configuration for web and mobile frontends.

## Install

```sh
pip install git+https://github.com/andreas-bergstrom/pykonf.git
```

## Usage

```sh
SECRET_KEY=secret DATA_FEATUREFLAGS_PAYMENT=value pykonf
```

Or via `python -m`:

```sh
SECRET_KEY=secret DATA_FEATUREFLAGS_PAYMENT=value python -m pykonf
```

## REST API Endpoints

All mutation endpoints (`PUT`, `POST`, `DELETE`) require a `secret_key` header matching `SECRET_KEY` and are rate-limited to 1/minute (shared across all mutations).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | — | Health check |
| `GET` | `/config` | — | Returns full config (Cache-Control: max-age=60) |
| `GET` | `/config/{path}` | — | Read nested value (e.g. `/config/featureflags/payment`) |
| `PUT` | `/config` | `secret_key` | Deep-merge partial update |
| `POST` | `/config/{path}` | `secret_key` | Set value at path. Body: `{"value": any}` or raw JSON |
| `DELETE` | `/config/{path}` | `secret_key` | Remove key at path |

## MCP Tools

The MCP server runs on the same process at `/mcp` (Streamable HTTP transport). Connect from Claude Code, VS Code, or any MCP client.

| Tool | Parameters | Description |
|------|-----------|-------------|
| `read_config` | `path` (optional) | Read full config or subtree at slash-separated path |
| `list_keys` | `path` (optional) | List keys under a path |
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

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — **(required)** | Secret key for mutation authorization |
| `CONFIG_FILE` | `config.json` | Path to persistent config file |
| `DATA_*` | — | Seed/override config on startup (underscore-separated → nested keys) |
| `DISABLE_RATE_LIMIT` | — | Set to `true`/`1`/`yes` to disable mutation rate limiting |
| `MUTATION_COOLDOWN` | `60` | Seconds between allowed mutations |

## Persistence

Configuration is loaded from `CONFIG_FILE` (default `config.json`) at startup.
`DATA_*` env vars are applied on top, so you can override specific values per deployment.
Changes via mutations are written back to the file immediately.
