from typing import Any
from fastapi import FastAPI, HTTPException, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.routing import Mount, compile_path, Match

from pykonf import config as cfg

try:
    from pykonf.mcp import mcp_server

    _mcp_asgi = mcp_server.http_app(path="/")
    _has_mcp = True
except ImportError:
    _mcp_asgi = None
    _has_mcp = False


app = FastAPI(
    lifespan=_mcp_asgi.lifespan if _has_mcp else None,
    title="pykonf",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if _has_mcp:

    class _MCPMount(Mount):
        def __init__(self, path):
            super().__init__(path, app=self._proxy)
            self.path_regex, _, _ = compile_path(self.path + "{path:path}")

        async def _proxy(self, scope, receive, send):
            remaining = scope.get("path_params", {}).get("path", "")
            scope["path"] = "/" + remaining if remaining else "/"
            scope["path"] = scope["path"].rstrip("/") or "/"
            del scope["path_params"]
            del scope["endpoint"]
            await _mcp_asgi(scope, receive, send)

        def matches(self, scope):
            if scope["type"] not in ("http", "websocket"):
                return Match.NONE, {}
            route_path = scope.get("path", "")
            root_path = scope.get("root_path", "")
            if root_path and route_path.startswith(root_path):
                route_path = route_path[len(root_path) :]
            match = self.path_regex.match(route_path)
            if match:
                matched_params = match.groupdict()
                child_scope = {
                    "path_params": matched_params,
                    "endpoint": self._proxy,
                }
                return Match.FULL, child_scope
            return Match.NONE, {}

    app.router.routes.append(_MCPMount("/mcp"))
    print("MCP server mounted at /mcp")


def verify_secret(secret_key: str | None) -> None:
    if secret_key != cfg.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def verify_read_key(read_key: str | None) -> None:
    if read_key != cfg.READ_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def mutate(do):
    try:
        cfg.check_mutation_rate()
        do()
        cfg.save_config(cfg.json_data)
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/config")
async def read_config(read_key: str | None = Header(None)):
    verify_read_key(read_key)
    return JSONResponse(
        content=cfg.json_data,
        media_type="application/json",
        headers={"Cache-Control": "max-age=60"},
    )


@app.get("/config/{path:path}")
async def read_config_path(path: str, read_key: str | None = Header(None)):
    verify_read_key(read_key)
    try:
        value = cfg.get_at_path(cfg.json_data, path)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return JSONResponse(content=value, media_type="application/json")


@app.put("/config")
async def update_config(
    data: dict = Body(...),
    secret_key: str | None = Header(None),
):
    verify_secret(secret_key)
    mutate(lambda: cfg.deep_merge(cfg.json_data, data))
    return {"message": "Configuration updated"}


@app.post("/config/{path:path}")
async def set_config_path(
    path: str,
    body: Any = Body(None),
    secret_key: str | None = Header(None),
):
    verify_secret(secret_key)

    if isinstance(body, dict) and "value" in body:
        value = body["value"]
    else:
        value = body

    mutate(lambda: cfg.set_at_path(cfg.json_data, path, value))
    return {"message": "Configuration updated"}


@app.delete("/config/{path:path}")
async def delete_config_path(
    path: str,
    secret_key: str | None = Header(None),
):
    verify_secret(secret_key)
    try:
        mutate(lambda: cfg.delete_at_path(cfg.json_data, path))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Configuration deleted"}


def main():
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    main()
