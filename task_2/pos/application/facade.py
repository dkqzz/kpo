"""Application facade for rubric and evaluation use cases."""

from pathlib import Path

from pos.domain.errors import DuplicateEntryError, EvaluationNotFoundError
from pos.domain.factories import EvaluationFactory
from pos.domain.model import AssessmentCriterion, Evaluation, Student, StudentResult
from pos.domain.ports import (
    CriterionRepository,
    EvaluationRepository,
    ResultExporter,
    StudentRepository,
)
from pos.domain.services import StudentResultCalculator

from .views import EvaluationView


class PosFacade:
    """Structural Facade that exposes the module's use cases to the console."""

    def __init__(
        self,
        students: StudentRepository,
        criteria: CriterionRepository,
        evaluations: EvaluationRepository,
        evaluation_factory: EvaluationFactory,
        result_calculator: StudentResultCalculator,
        result_exporter: ResultExporter,
    ) -> None:
        self._students = students
        self._criteria = criteria
        self._evaluations = evaluations
        self._evaluation_factory = evaluation_factory
        self._result_calculator = result_calculator
        self._result_exporter = result_exporter

    def add_student(self, student_id: str, name: str) -> Student:
        student = Student(student_id, name)
        self._students.add(student)
        return student

    def list_students(self) -> tuple[Student, ...]:
        return self._students.list_all()

    def add_criterion(
        self, criterion_id: str, name: str, max_score: object, weight: object
    ) -> AssessmentCriterion:
        criterion = AssessmentCriterion(criterion_id, name, max_score, weight)
        self._criteria.add(criterion)
        return criterion

    def list_criteria(self) -> tuple[AssessmentCriterion, ...]:
        return self._criteria.list_all()

    def assign_evaluation(
        self,
        student_id: str,
        criterion_id: str,
        score: object,
        comment: str = "",
    ) -> Evaluation:
        student = self._students.get(student_id)
        criterion = self._criteria.get(criterion_id)
        try:
            self._evaluations.get(student_id, criterion_id)
        except EvaluationNotFoundError:
            pass
        else:
            raise DuplicateEntryError("Для этого студента и критерия оценка уже есть")
        evaluation = self._evaluation_factory.create(student, criterion, score, comment)
        self._evaluations.add(evaluation)
        return evaluation

    def update_evaluation(
        self,
        student_id: str,
        criterion_id: str,
        score: object,
        comment: str = "",
    ) -> Evaluation:
        self._evaluations.get(student_id, criterion_id)
        student = self._students.get(student_id)
        criterion = self._criteria.get(criterion_id)
        evaluation = self._evaluation_factory.create(student, criterion, score, comment)
        self._evaluations.update(evaluation)
        return evaluation

    def cancel_evaluation(self, student_id: str, criterion_id: str) -> None:
        self._evaluations.get(student_id, criterion_id)
        self._evaluations.delete(student_id, criterion_id)

    def list_evaluations(self, student_id: str) -> tuple[EvaluationView, ...]:
        self._students.get(student_id)
        views = []
        for evaluation in self._evaluations.for_student(student_id):
            criterion = self._criteria.get(evaluation.criterion_id)
            views.append(
                EvaluationView(
                    student_id=evaluation.student_id,
                    criterion_id=evaluation.criterion_id,
                    criterion_name=criterion.name,
                    score=evaluation.score.value,
                    max_score=evaluation.score.max_score,
                    comment=evaluation.comment,
                )
            )
        return tuple(views)

    def calculate_result(self, student_id: str) -> StudentResult:
        student = self._students.get(student_id)
        return self._result_calculator.calculate(
            student,
            self._evaluations.for_student(student_id),
            self._criteria.list_all(),
        )

    def calculate_all_results(self) -> tuple[StudentResult, ...]:
        return tuple(
            self.calculate_result(student.student_id)
            for student in self._students.list_all()
        )

    def export_totals(self, destination: str | Path) -> Path:
        return self._result_exporter.export(
            self.calculate_all_results(), destination
        )
