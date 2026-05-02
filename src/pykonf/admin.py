from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi import Request
from nicegui import ui
import json
from typing import Dict

users = [("user1", "pass1"), ("user2", "pass2")]
session_info: Dict[str, Dict] = {}


def is_authenticated(request: Request) -> bool:
    return session_info.get(request.session.get("id"), {}).get("authenticated", False)


def init(app: FastAPI, json_data) -> None:
    @ui.page("/admin")
    def show():
        columns = [
            {
                "name": "key_name",
                "label": "Key name",
                "field": "key_name",
                "required": True,
                "align": "left",
            },
            {
                "name": "key_data",
                "label": "Key data",
                "field": "key_data",
                "sortable": True,
            },
        ]
        rows = [
            {"key_name": key, "key_data": json.dumps(value)}
            for key, value in json_data.items()
        ]

        ui.html("<h1>Current configuration</h1>")
        ui.table(columns=columns, rows=rows, row_key="key")

    ui.run_with(app)
