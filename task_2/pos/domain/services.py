"""Domain service and strategy for calculating current weighted results."""

from collections.abc import Mapping, Sequence
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Protocol

from .errors import ValidationError
from .model import AssessmentCriterion, Evaluation, Student, StudentResult, decimal_value


class ResultCalculationStrategy(Protocol):
    """Behavioral policy for turning rubric evaluations into a course result."""

    def calculate(
        self,
        evaluations: Sequence[Evaluation],
        criteria_by_id: Mapping[str, AssessmentCriterion],
        max_total: Decimal,
    ) -> Decimal | None:
        ...


class WeightedAverageStrategy:
    """Calculate a weighted average over the criteria that have been graded."""

    def calculate(
        self,
        evaluations: Sequence[Evaluation],
        criteria_by_id: Mapping[str, AssessmentCriterion],
        max_total: Decimal,
    ) -> Decimal | None:
        if not evaluations:
            return None

        weighted_sum = Decimal("0")
        weight_sum = Decimal("0")
        seen_criteria: set[str] = set()
        for evaluation in evaluations:
            if evaluation.criterion_id in seen_criteria:
                raise ValidationError("На один критерий найдено несколько оценок")
            seen_criteria.add(evaluation.criterion_id)
            criterion = criteria_by_id.get(evaluation.criterion_id)
            if criterion is None:
                raise ValidationError("Оценка ссылается на отсутствующий критерий")
            if evaluation.score.max_score != criterion.max_score:
                raise ValidationError("Максимум оценки не совпадает с максимумом критерия")
            weighted_sum += (
                evaluation.score.value / criterion.max_score
            ) * criterion.weight
            weight_sum += criterion.weight

        if weight_sum <= 0:
            raise ValidationError("Для расчёта нужен хотя бы один критерий с положительным весом")
        with localcontext() as context:
            context.prec = 28
            total = max_total * weighted_sum / weight_sum
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class StudentResultCalculator:
    """Domain service that calculates a student's current result."""

    def __init__(
        self,
        strategy: ResultCalculationStrategy,
        max_total: Decimal = Decimal("10"),
    ) -> None:
        max_total = decimal_value(max_total, "Максимальный итог")
        if max_total <= 0:
            raise ValidationError("Максимальный итог должен быть больше нуля")
        self._strategy = strategy
        self._max_total = max_total

    def calculate(
        self,
        student: Student,
        evaluations: Sequence[Evaluation],
        criteria: Sequence[AssessmentCriterion],
    ) -> StudentResult:
        if any(item.student_id != student.student_id for item in evaluations):
            raise ValidationError("В расчёт попала оценка другого студента")
        criteria_by_id = {criterion.criterion_id: criterion for criterion in criteria}
        total = self._strategy.calculate(evaluations, criteria_by_id, self._max_total)
        return StudentResult(
            student_id=student.student_id,
            student_name=student.name,
            total_score=total,
            max_total=self._max_total,
            graded_criteria=len(evaluations),
            total_criteria=len(criteria),
        )
