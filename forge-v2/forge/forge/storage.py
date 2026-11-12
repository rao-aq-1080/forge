import json
import sqlite3
from pathlib import Path

from forge.config import settings


def get_connection() -> sqlite3.Connection:
    database = Path(settings.database_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                requirement TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS approved_snapshots (
                project_id TEXT NOT NULL,
                files_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, created_at)
            )
            """
        )
        connection.commit()


def save_project(
    project_id: str,
    project_name: str,
    requirement: str,
    status: str,
    result: dict,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """INSERT OR REPLACE INTO projects
               (id, project_name, requirement, status, result_json)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, project_name, requirement, status, json.dumps(result)),
        )
        connection.commit()


def get_project(project_id: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["result"] = json.loads(data.pop("result_json"))
        return data


def update_project_status(project_id: str, status: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE projects SET status = ? WHERE id = ?",
            (status, project_id),
        )
        connection.commit()


def list_projects(limit: int = 50) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM projects ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def list_approved_projects(limit: int = 200) -> list[dict]:
    """All approved projects with full result, used to build the RAG corpus."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM projects WHERE status = 'approved' "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            try:
                d["result"] = json.loads(d.pop("result_json"))
            except json.JSONDecodeError:
                d["result"] = {}
            out.append(d)
        return out


def save_approved_snapshot(project_id: str, files: list[dict]) -> None:
    """Store the approved file set for later diffing against future versions."""
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM approved_snapshots WHERE project_id = ?",
            (project_id,),
        )
        connection.execute(
            """INSERT INTO approved_snapshots (project_id, files_json)
               VALUES (?, ?)""",
            (project_id, json.dumps(files)),
        )
        connection.commit()


def get_approved_snapshot(project_id: str) -> list[dict] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT files_json FROM approved_snapshots WHERE project_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["files_json"])
        except json.JSONDecodeError:
            return None
