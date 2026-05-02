# pykonf — Agent Guide

## Run the API

```sh
SECRET_KEY=secret DATA_FEATUREFLAGS_PAYMENT=value python api.py
```

Or after `pip install -e .`:

```sh
SECRET_KEY=secret DATA_FEATUREFLAGS_PAYMENT=value pykonf
```

Required env vars: `SECRET_KEY` (checked at import time, absent raises).

Config is seeded from `DATA_*` env vars at startup (underscore-separated keys → nested dict), then persisted to `CONFIG_FILE` (default `config.json`). `GET /config` returns current config; `PUT /config` updates it (deep-merge, rate-limited to 1/minute, requires `secret_key` header matching `SECRET_KEY`).

## Endpoints

- `GET /health` — health check
- `GET /config` — returns current configuration (Cache-Control: max-age=60)
- `PUT /config` — deep-merge partial update (rate-limited, requires `secret_key` header)

## Known Issues

- **Dead code in `admin.py`**: unused (init call removed), standalone nicegui-based admin UI
- **No tests**, no CI, no lint config
- **No `pyproject.toml` / `setup.py`** — not a standard Python package
- **Pydantic v2** (`RootModel` with `root` field)
- **`requirements.txt`** has many unused transitive deps (matplotlib, plotly, Pillow, pyobjc, etc.)

## Commands

```sh
# format (only tool configured)
black api.py admin.py
```
