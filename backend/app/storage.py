"""Small SQLite incident store, separate from Hindsight's semantic memory."""
from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Any, Iterator

from app.config import get_settings


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_storage() -> None:
    with _connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                problem TEXT NOT NULL,
                category TEXT,
                technology TEXT,
                error TEXT,
                root_cause TEXT,
                solution TEXT,
                outcome TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_conversation_messages(conversation_id: str, *, limit: int = 20) -> list[dict[str, str]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT role, content FROM conversation_messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
            (conversation_id, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def save_conversation_message(conversation_id: str, role: str, content: str) -> None:
    with _connect() as connection:
        connection.execute(
            "INSERT INTO conversation_messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content),
        )


def save_incident(conversation_id: str | None, incident: dict[str, Any]) -> None:
    if not incident.get("problem"):
        return
    with _connect() as connection:
        existing = connection.execute(
            "SELECT id FROM incidents WHERE conversation_id = ? ORDER BY id DESC LIMIT 1",
            (conversation_id,),
        ).fetchone() if conversation_id else None
        values = (
            incident.get("problem"), incident.get("category"), incident.get("technology"),
            incident.get("error"), incident.get("root_cause"), incident.get("solution"), incident.get("outcome"),
        )
        if existing:
            connection.execute(
                """UPDATE incidents SET problem = ?, category = COALESCE(?, category),
                   technology = COALESCE(?, technology), error = COALESCE(?, error),
                   root_cause = COALESCE(?, root_cause), solution = COALESCE(?, solution),
                   outcome = COALESCE(?, outcome) WHERE id = ?""",
                (*values, existing["id"]),
            )
        else:
            connection.execute(
                """INSERT INTO incidents (conversation_id, problem, category, technology, error, root_cause, solution, outcome)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (conversation_id, *values),
            )


def list_incidents() -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def recurring_problems() -> list[dict[str, Any]]:
    return list_incidents()
