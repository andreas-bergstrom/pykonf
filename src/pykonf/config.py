import json
import os
import time
from typing import Any

SECRET_KEY = os.environ.get("SECRET_KEY")
if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY environment variable is not set.")

CONFIG_FILE = os.environ.get("CONFIG_FILE", "config.json")

MUTATION_COOLDOWN = float(os.environ.get("MUTATION_COOLDOWN", "60"))
DISABLE_RATE_LIMIT = os.environ.get("DISABLE_RATE_LIMIT", "").lower() in (
    "true",
    "1",
    "yes",
)

_last_mutation_time: float = 0.0


def check_mutation_rate() -> None:
    if DISABLE_RATE_LIMIT:
        return
    global _last_mutation_time
    now = time.monotonic()
    if now - _last_mutation_time < MUTATION_COOLDOWN:
        raise RuntimeError("Mutation rate limit exceeded (1 per minute)")
    _last_mutation_time = now


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


def get_at_path(config: dict, path: str) -> Any:
    if not path:
        return config
    keys = path.strip("/").split("/")
    target = config
    for key in keys:
        if not isinstance(target, dict) or key not in target:
            raise KeyError(f"Key not found: {path}")
        target = target[key]
    return target


def set_at_path(config: dict, path: str, value: Any) -> None:
    if not path:
        raise ValueError("Cannot set root")
    keys = path.strip("/").split("/")
    target = config
    for key in keys[:-1]:
        if not isinstance(target, dict):
            raise ValueError(f"Cannot traverse into non-dict: {key}")
        target = target.setdefault(key, {})
    if not isinstance(target, dict):
        raise ValueError(f"Cannot traverse into non-dict: {keys[-1]}")
    target[keys[-1]] = value


def delete_at_path(config: dict, path: str) -> None:
    if not path:
        raise ValueError("Cannot delete root")
    keys = path.strip("/").split("/")
    target = config
    for key in keys[:-1]:
        if not isinstance(target, dict) or key not in target:
            raise KeyError(f"Key not found: {path}")
        target = target[key]
    try:
        del target[keys[-1]]
    except KeyError:
        raise KeyError(f"Key not found: {path}")


json_data = load_config()
print(f"Loaded config: {json.dumps(json_data, indent=2)}")
