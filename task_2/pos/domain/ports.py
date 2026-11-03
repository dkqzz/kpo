"""Repository and export ports used by the application layer."""

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from .model import AssessmentCriterion, Evaluation, Student, StudentResult


class StudentRepository(Protocol):
    def add(self, student: Student) -> None:
        ...

    def get(self, student_id: str) -> Student:
        ...

    def list_all(self) -> tuple[Student, ...]:
        ...


class CriterionRepository(Protocol):
    def add(self, criterion: AssessmentCriterion) -> None:
        ...

    def get(self, criterion_id: str) -> AssessmentCriterion:
        ...

    def list_all(self) -> tuple[AssessmentCriterion, ...]:
        ...


class EvaluationRepository(Protocol):
    def add(self, evaluation: Evaluation) -> None:
        ...

    def update(self, evaluation: Evaluation) -> None:
        ...

    def get(self, student_id: str, criterion_id: str) -> Evaluation:
        ...

    def delete(self, student_id: str, criterion_id: str) -> None:
        ...

    def for_student(self, student_id: str) -> tuple[Evaluation, ...]:
        ...

    def list_all(self) -> tuple[Evaluation, ...]:
        ...


class ResultExporter(Protocol):
    def export(
        self, results: Sequence[StudentResult], destination: str | Path
    ) -> Path:
        ...
