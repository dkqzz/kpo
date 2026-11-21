"""Build reports stored independently from the submission database."""

from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from common.database import connect

from .checker import BuildStatus


class Report(TypedDict):
    submission_id: str
    assignment_id: str
    status: BuildStatus
    success: bool
    details: str
    checked_at: str


class ReportRepository:
    def __init__(self, data_dir: Path) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self._database = data_dir / "reports.sqlite3"
        with connect(self._database) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS reports (
                    submission_id TEXT PRIMARY KEY,
                    assignment_id TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('passed', 'failed')),
                    details TEXT NOT NULL,
                    checked_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS reports_by_assignment ON reports (assignment_id);
            """)

    def save(self, submission_id: str, assignment_id: str, status: BuildStatus, details: str) -> Report:
        checked_at = datetime.now(UTC).isoformat(timespec="microseconds")
        with connect(self._database) as connection:
            connection.execute("""
                INSERT INTO reports VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(submission_id) DO NOTHING
            """, (submission_id, assignment_id, status, details, checked_at))
            row = connection.execute(
                "SELECT * FROM reports WHERE submission_id = ?", (submission_id,)
            ).fetchone()
        return Report(**dict(row), success=row["status"] == "passed")

    def get(self, submission_id: str) -> Report | None:
        with connect(self._database) as connection:
            row = connection.execute(
                "SELECT * FROM reports WHERE submission_id = ?", (submission_id,)
            ).fetchone()
        return Report(**dict(row), success=row["status"] == "passed") if row is not None else None

    def for_assignment(self, assignment_id: str) -> list[Report]:
        with connect(self._database) as connection:
            rows = connection.execute(
                "SELECT * FROM reports WHERE assignment_id = ?", (assignment_id,)
            ).fetchall()
        return [Report(**dict(row), success=row["status"] == "passed") for row in rows]
