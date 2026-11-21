"""Persist submission metadata and store immutable artifacts by ID."""

from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from common.database import connect


class Submission(TypedDict):
    submission_id: str
    student_id: str
    assignment_id: str
    filename: str
    size_bytes: int
    submitted_at: str


class SubmissionRepository:
    def __init__(self, data_dir: Path) -> None:
        self._artifacts = data_dir / "artifacts"
        self._artifacts.mkdir(parents=True, exist_ok=True)
        self._database = data_dir / "submissions.sqlite3"
        with connect(self._database) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS submissions (
                    submission_id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    assignment_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    submitted_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS submissions_by_assignment
                    ON submissions (assignment_id, submitted_at, submission_id);
            """)

    def add(self, student_id: str, assignment_id: str, filename: str, content: bytes) -> Submission:
        submission = Submission(
            submission_id=str(uuid4()),
            student_id=student_id,
            assignment_id=assignment_id,
            filename=filename,
            size_bytes=len(content),
            submitted_at=datetime.now(UTC).isoformat(timespec="microseconds"),
        )
        artifact = self.artifact_path(submission["submission_id"])
        stored_file = artifact.open("xb")
        try:
            with stored_file:
                stored_file.write(content)
            with connect(self._database) as connection:
                connection.execute("""
                    INSERT INTO submissions VALUES (
                        :submission_id, :student_id, :assignment_id,
                        :filename, :size_bytes, :submitted_at
                    )
                """, submission)
        except Exception:
            artifact.unlink(missing_ok=True)
            raise
        return submission

    def get(self, submission_id: str) -> Submission | None:
        with connect(self._database) as connection:
            row = connection.execute(
                "SELECT * FROM submissions WHERE submission_id = ?", (submission_id,)
            ).fetchone()
        return Submission(**dict(row)) if row is not None else None

    def for_assignment(self, assignment_id: str) -> list[Submission]:
        with connect(self._database) as connection:
            rows = connection.execute("""
                SELECT * FROM submissions WHERE assignment_id = ?
                ORDER BY submitted_at DESC, submission_id DESC
            """, (assignment_id,)).fetchall()
        return [Submission(**dict(row)) for row in rows]

    def artifact_path(self, submission_id: str) -> Path:
        return self._artifacts / submission_id
