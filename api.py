from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Body, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import RootModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json
import os
from typing import Dict, Union

SECRET_KEY = os.environ.get("SECRET_KEY")
if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY environment variable is not set.")

CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.json")


def load_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                config = json.load(f)
        else:
            config = {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not load config file: {e}")
        config = {}

    for key, value in sorted(os.environ.items()):
        if key.startswith("DATA_"):
            levels = key.removeprefix("DATA_").split("_")
            target = config
            for level in levels[:-1]:
                level = level.lower()
                target = target.setdefault(level, {})
            target[levels[-1].lower()] = value

    return config


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def deep_merge(base: dict, update: dict) -> None:
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


json_data = load_config()
print(f"Loaded config: {json.dumps(json_data, indent=2)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan, title="pykonf", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class JsonData(RootModel):
    root: Dict[str, Union[str, "JsonData"]]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/config")
async def read_config():
    return JSONResponse(
        content=json_data,
        media_type="application/json",
        headers={"Cache-Control": "max-age=60"},
    )


@app.put("/config")
@limiter.limit("1/minute")
async def update_config(
    request: Request,
    data: JsonData = Body(...),
    secret_key: str = Header(None),
):
    if secret_key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    update = data.model_dump(mode="json")
    deep_merge(json_data, update)
    save_config(json_data)

    return {"message": "Configuration updated"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(content={"error": exc.detail}, status_code=exc.status_code)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
