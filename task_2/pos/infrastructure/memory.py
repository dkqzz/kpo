"""In-memory repository adapters for a single interactive run."""

from pos.domain.errors import (
    DuplicateEntryError,
    EntityNotFoundError,
    EvaluationNotFoundError,
)
from pos.domain.model import AssessmentCriterion, Evaluation, Student


class InMemoryStudentRepository:
    def __init__(self) -> None:
        self._items: dict[str, Student] = {}

    def add(self, student: Student) -> None:
        if student.student_id in self._items:
            raise DuplicateEntryError(f"Студент с ID {student.student_id} уже существует")
        self._items[student.student_id] = student

    def get(self, student_id: str) -> Student:
        try:
            return self._items[student_id]
        except KeyError as exc:
            raise EntityNotFoundError(f"Студент с ID {student_id} не найден") from exc

    def list_all(self) -> tuple[Student, ...]:
        return tuple(self._items.values())


class InMemoryCriterionRepository:
    def __init__(self) -> None:
        self._items: dict[str, AssessmentCriterion] = {}

    def add(self, criterion: AssessmentCriterion) -> None:
        if criterion.criterion_id in self._items:
            raise DuplicateEntryError(f"Критерий с ID {criterion.criterion_id} уже существует")
        self._items[criterion.criterion_id] = criterion

    def get(self, criterion_id: str) -> AssessmentCriterion:
        try:
            return self._items[criterion_id]
        except KeyError as exc:
            raise EntityNotFoundError(f"Критерий с ID {criterion_id} не найден") from exc

    def list_all(self) -> tuple[AssessmentCriterion, ...]:
        return tuple(self._items.values())


class InMemoryEvaluationRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Evaluation] = {}

    def add(self, evaluation: Evaluation) -> None:
        key = (evaluation.student_id, evaluation.criterion_id)
        if key in self._items:
            raise DuplicateEntryError("Оценка для этой пары уже существует")
        self._items[key] = evaluation

    def update(self, evaluation: Evaluation) -> None:
        key = (evaluation.student_id, evaluation.criterion_id)
        if key not in self._items:
            raise EvaluationNotFoundError("Оценка для этой пары не найдена")
        self._items[key] = evaluation

    def get(self, student_id: str, criterion_id: str) -> Evaluation:
        try:
            return self._items[(student_id, criterion_id)]
        except KeyError as exc:
            raise EvaluationNotFoundError("Оценка для этой пары не найдена") from exc

    def delete(self, student_id: str, criterion_id: str) -> None:
        key = (student_id, criterion_id)
        if key not in self._items:
            raise EvaluationNotFoundError("Оценка для этой пары не найдена")
        del self._items[key]

    def for_student(self, student_id: str) -> tuple[Evaluation, ...]:
        return tuple(
            evaluation
            for (stored_student_id, _), evaluation in self._items.items()
            if stored_student_id == student_id
        )

    def list_all(self) -> tuple[Evaluation, ...]:
        return tuple(self._items.values())
