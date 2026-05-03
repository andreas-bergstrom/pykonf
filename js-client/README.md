# pykonf JS Client Reference

A minimal reference app demonstrating how a JavaScript client reads configuration from a pykonf server.

## Usage

1. Start pykonf:

```sh
SECRET_KEY=secret READ_KEY=read DATA_FEATUREFLAGS_PAYMENT=value pykonf
```

2. Open `index.html` in a browser (or serve with any static server).

3. Enter the server URL and read key, then click a button to fetch config.

## API Calls Demonstrated

| Action | Endpoint | Header |
|--------|----------|--------|
| Fetch all config | `GET /config` | `read-key` |
| Fetch nested value | `GET /config/{path}` | `read-key` |

## Notes

- This app uses vanilla JavaScript with zero dependencies. No build tools or npm needed.
- CORS is already enabled on the pykonf server, so it works cross-origin.
- The `read-key` header is how the server authenticates read requests.
- This directory is **not** part of the Python package and will not be included in `pip`/`pipx` installs.
