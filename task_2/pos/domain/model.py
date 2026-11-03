"""Domain entities and value objects for rubric-based assessment."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .errors import ValidationError


def decimal_value(value: object, label: str) -> Decimal:
    if isinstance(value, bool):
        raise ValidationError(f"{label} должно быть числом")
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError, AttributeError) as exc:
        raise ValidationError(f"{label} должно быть числом") from exc
    if not result.is_finite():
        raise ValidationError(f"{label} должно быть конечным числом")
    return result


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} не может быть пустым")
    return value.strip()


@dataclass(frozen=True)
class Student:
    """A student identified by a stable course-local identifier."""

    student_id: str
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "student_id", _required_text(self.student_id, "ID студента"))
        object.__setattr__(self, "name", _required_text(self.name, "Имя студента"))


@dataclass(frozen=True)
class AssessmentCriterion:
    """One rubric criterion with its maximum score and relative weight."""

    criterion_id: str
    name: str
    max_score: Decimal
    weight: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "criterion_id", _required_text(self.criterion_id, "ID критерия"))
        object.__setattr__(self, "name", _required_text(self.name, "Название критерия"))
        maximum = decimal_value(self.max_score, "Максимальный балл")
        weight = decimal_value(self.weight, "Вес критерия")
        if maximum <= 0:
            raise ValidationError("Максимальный балл должен быть больше нуля")
        if weight <= 0:
            raise ValidationError("Вес критерия должен быть больше нуля")
        object.__setattr__(self, "max_score", maximum)
        object.__setattr__(self, "weight", weight)


@dataclass(frozen=True)
class BoundedScore:
    """A score value object that cannot exceed its rubric maximum."""

    value: Decimal
    max_score: Decimal

    def __post_init__(self) -> None:
        value = decimal_value(self.value, "Оценка")
        maximum = decimal_value(self.max_score, "Максимальный балл")
        if maximum <= 0:
            raise ValidationError("Максимальный балл должен быть больше нуля")
        if value < 0 or value > maximum:
            raise ValidationError(
                f"Оценка должна быть от 0 до {format(maximum, 'f')}"
            )
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "max_score", maximum)


@dataclass(frozen=True)
class Evaluation:
    """A student's evaluation for one rubric criterion.

    Its natural identity is the student/criterion pair, so correcting a mark
    replaces the value for that pair and cancelling removes it.
    """

    student_id: str
    criterion_id: str
    score: BoundedScore
    comment: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "student_id", _required_text(self.student_id, "ID студента"))
        object.__setattr__(
            self, "criterion_id", _required_text(self.criterion_id, "ID критерия")
        )
        if not isinstance(self.score, BoundedScore):
            raise ValidationError("Оценка должна быть значением BoundedScore")
        if not isinstance(self.comment, str):
            raise ValidationError("Комментарий должен быть текстом")
        object.__setattr__(self, "comment", self.comment.strip())


@dataclass(frozen=True)
class StudentResult:
    """Calculated current course result for a student."""

    student_id: str
    student_name: str
    total_score: Decimal | None
    max_total: Decimal
    graded_criteria: int
    total_criteria: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "student_id", _required_text(self.student_id, "ID студента"))
        object.__setattr__(self, "student_name", _required_text(self.student_name, "Имя студента"))
        maximum = decimal_value(self.max_total, "Максимальный итог")
        if maximum <= 0:
            raise ValidationError("Максимальный итог должен быть больше нуля")
        if self.graded_criteria < 0 or self.total_criteria < 0:
            raise ValidationError("Количество критериев не может быть отрицательным")
        if self.graded_criteria > self.total_criteria:
            raise ValidationError("Оценённых критериев больше, чем критериев в рубрикаторе")
        total = self.total_score
        if total is None and self.graded_criteria:
            raise ValidationError("При наличии оценок итог должен быть рассчитан")
        if total is not None and not self.graded_criteria:
            raise ValidationError("Без оценок итог не может быть рассчитан")
        if total is not None:
            total = decimal_value(total, "Итоговый балл")
            if total < 0 or total > maximum:
                raise ValidationError("Итоговый балл вышел за допустимый диапазон")
        object.__setattr__(self, "max_total", maximum)
        object.__setattr__(self, "total_score", total)
