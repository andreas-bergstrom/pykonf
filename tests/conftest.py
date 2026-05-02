import os
import json
import tempfile
from collections.abc import Iterator

import pytest
from starlette.testclient import TestClient

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DISABLE_RATE_LIMIT"] = "true"
os.environ["CONFIG_FILE"] = tempfile.mktemp(suffix=".json")

from pykonf import config as cfg
from pykonf.api import app


@pytest.fixture(autouse=True)
def reset_config_state():
    state = cfg._last_mutation_time
    cfg._last_mutation_time = 0.0
    cfg.json_data = {}
    yield
    cfg._last_mutation_time = state


@pytest.fixture
def config_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"host": "localhost", "port": 8080}, f)
        path = f.name
    os.environ["CONFIG_FILE"] = path
    cfg.CONFIG_FILE = path
    yield path
    os.unlink(path)
    os.environ["CONFIG_FILE"] = tempfile.mktemp(suffix=".json")
    cfg.CONFIG_FILE = os.environ["CONFIG_FILE"]


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"secret-key": "test-secret-key"}
