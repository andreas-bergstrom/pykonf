# pykonf

Simple HTTP API to set and retrieve client configuration for web and mobile frontends.

## Install

```sh
pip install git+https://github.com/andreas-bergstrom/pykonf.git
```

Or install with optional admin UI:

```sh
pip install "pykonf[admin] @ git+https://github.com/andreas-bergstrom/pykonf.git"
```

## Usage

```sh
SECRET_KEY=secret DATA_FEATUREFLAGS_PAYMENT=value pykonf
```

Or via `python -m`:

```sh
SECRET_KEY=secret DATA_FEATUREFLAGS_PAYMENT=value python -m pykonf
```

## Endpoints

| Method | Path       | Auth           | Rate limited | Description                    |
|--------|------------|----------------|--------------|--------------------------------|
| GET    | `/health`  | No             | No           | Health check                   |
| GET    | `/config`  | No             | No           | Returns current configuration  |
| PUT    | `/config`  | `secret_key` header | 1/minute | Merge partial update into config |

## Environment variables

| Variable       | Default        | Description                                    |
|----------------|----------------|------------------------------------------------|
| `SECRET_KEY`   | — **(required)** | Secret key for `PUT /config` authorization    |
| `CONFIG_FILE`  | `config.json`  | Path to persistent config file                 |
| `DATA_*`       | —              | Seed/override config on startup (underscore-separated → nested keys) |

## Persistence

Configuration is loaded from `CONFIG_FILE` (default `config.json`) at startup.
`DATA_*` env vars are applied on top, so you can override specific values per deployment.
Changes via `PUT /config` are written back to the file immediately.
