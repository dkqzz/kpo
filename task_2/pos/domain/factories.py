"""Factories for constructing evaluations from existing rubric entities."""

from abc import ABC, abstractmethod

from .model import AssessmentCriterion, BoundedScore, Evaluation, Student


class EvaluationFactory(ABC):
    """GoF Factory Method abstraction used when assigning a mark."""

    @abstractmethod
    def create(
        self,
        student: Student,
        criterion: AssessmentCriterion,
        score: object,
        comment: str = "",
    ) -> Evaluation:
        ...


class RubricEvaluationFactory(EvaluationFactory):
    """Concrete creator that applies the criterion's score bound."""

    def create(
        self,
        student: Student,
        criterion: AssessmentCriterion,
        score: object,
        comment: str = "",
    ) -> Evaluation:
        bounded_score = BoundedScore(score, criterion.max_score)
        return Evaluation(
            student_id=student.student_id,
            criterion_id=criterion.criterion_id,
            score=bounded_score,
            comment=comment,
        )
