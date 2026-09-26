from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "acip.db"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def fetch_all(query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with connect() as connection:
        return [dict(row) for row in connection.execute(query, tuple(params)).fetchall()]


def fetch_one(query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(query, tuple(params)).fetchone()
        return dict(row) if row else None


def scalar(query: str, params: Iterable[Any] = (), default: Any = 0) -> Any:
    row = fetch_one(query, params)
    return next(iter(row.values())) if row else default
