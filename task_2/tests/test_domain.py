import unittest
from decimal import Decimal

from pos.domain.errors import ValidationError
from pos.domain.factories import RubricEvaluationFactory
from pos.domain.model import AssessmentCriterion, BoundedScore, Student
from pos.domain.services import StudentResultCalculator, WeightedAverageStrategy


class DomainModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.student = Student("S-001", "Анна")
        self.first = AssessmentCriterion("C-001", "Проект", "10", "2")
        self.second = AssessmentCriterion("C-002", "Защита", "20", "3")
        self.factory = RubricEvaluationFactory()

    def test_student_and_criterion_normalize_text_and_decimals(self) -> None:
        student = Student(" S-002 ", " Борис ")
        criterion = AssessmentCriterion(" C-003 ", " Эссе ", "5", "1.5")

        self.assertEqual((student.student_id, student.name), ("S-002", "Борис"))
        self.assertEqual(criterion.max_score, Decimal("5"))
        self.assertEqual(criterion.weight, Decimal("1.5"))

    def test_empty_names_and_non_positive_criterion_values_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Student("S-003", "   ")
        with self.assertRaises(ValidationError):
            AssessmentCriterion("C-004", "Критерий", "0", "1")
        with self.assertRaises(ValidationError):
            AssessmentCriterion("C-005", "Критерий", "10", "0")
        with self.assertRaises(ValidationError):
            AssessmentCriterion("C-006", "Критерий", "NaN", "1")

    def test_bounded_score_accepts_edges_and_rejects_out_of_range(self) -> None:
        self.assertEqual(BoundedScore("0", "10").value, Decimal("0"))
        self.assertEqual(BoundedScore("10", "10").value, Decimal("10"))
        with self.assertRaises(ValidationError):
            BoundedScore("10.01", "10")
        with self.assertRaises(ValidationError):
            BoundedScore("-0.01", "10")

    def test_factory_creates_evaluation_linked_to_student_and_criterion(self) -> None:
        evaluation = self.factory.create(self.student, self.first, "8", "Хорошо")

        self.assertEqual(evaluation.student_id, self.student.student_id)
        self.assertEqual(evaluation.criterion_id, self.first.criterion_id)
        self.assertEqual(evaluation.score.value, Decimal("8"))
        self.assertEqual(evaluation.comment, "Хорошо")

    def test_weighted_total_uses_criterion_weights_and_returns_score_out_of_ten(self) -> None:
        evaluations = (
            self.factory.create(self.student, self.first, "8"),
            self.factory.create(self.student, self.second, "15"),
        )
        calculator = StudentResultCalculator(WeightedAverageStrategy())

        result = calculator.calculate(self.student, evaluations, (self.first, self.second))

        self.assertEqual(result.total_score, Decimal("7.70"))
        self.assertEqual(result.max_total, Decimal("10"))
        self.assertEqual(result.graded_criteria, 2)
        self.assertEqual(result.total_criteria, 2)

    def test_partial_result_normalizes_weights_over_evaluated_criteria(self) -> None:
        evaluation = self.factory.create(self.student, self.first, "8")
        calculator = StudentResultCalculator(WeightedAverageStrategy())

        result = calculator.calculate(self.student, (evaluation,), (self.first, self.second))

        self.assertEqual(result.total_score, Decimal("8.00"))
        self.assertEqual(result.graded_criteria, 1)
        self.assertEqual(result.total_criteria, 2)

    def test_result_rounds_half_up_to_two_decimal_places(self) -> None:
        criterion = AssessmentCriterion("C-003", "Точная оценка", "200", "1")
        evaluation = self.factory.create(self.student, criterion, "160.1")
        result = StudentResultCalculator(WeightedAverageStrategy()).calculate(
            self.student, (evaluation,), (criterion,)
        )

        self.assertEqual(result.total_score, Decimal("8.01"))

    def test_no_evaluations_means_no_result(self) -> None:
        result = StudentResultCalculator(WeightedAverageStrategy()).calculate(
            self.student, (), (self.first, self.second)
        )

        self.assertIsNone(result.total_score)
        self.assertEqual(result.graded_criteria, 0)

    def test_calculator_rejects_evaluation_for_another_student(self) -> None:
        other = Student("S-009", "Игорь")
        evaluation = self.factory.create(other, self.first, "5")

        with self.assertRaises(ValidationError):
            StudentResultCalculator(WeightedAverageStrategy()).calculate(
                self.student, (evaluation,), (self.first,)
            )


if __name__ == "__main__":
    unittest.main()
