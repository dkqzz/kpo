import unittest
from decimal import Decimal
from pathlib import Path

from pos.application.facade import PosFacade
from pos.domain.errors import DuplicateEntryError, EntityNotFoundError, EvaluationNotFoundError
from pos.domain.factories import RubricEvaluationFactory
from pos.domain.services import StudentResultCalculator, WeightedAverageStrategy
from pos.infrastructure.memory import (
    InMemoryCriterionRepository,
    InMemoryEvaluationRepository,
    InMemoryStudentRepository,
)


class RecordingExporter:
    def __init__(self) -> None:
        self.results = ()
        self.destination = None

    def export(self, results, destination: str | Path) -> Path:
        self.results = tuple(results)
        self.destination = Path(destination)
        return self.destination


class ApplicationFacadeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.exporter = RecordingExporter()
        self.facade = PosFacade(
            students=InMemoryStudentRepository(),
            criteria=InMemoryCriterionRepository(),
            evaluations=InMemoryEvaluationRepository(),
            evaluation_factory=RubricEvaluationFactory(),
            result_calculator=StudentResultCalculator(WeightedAverageStrategy()),
            result_exporter=self.exporter,
        )

    def seed(self) -> None:
        self.facade.add_student("S-101", "Мария")
        self.facade.add_criterion("C-101", "Практика", "10", "2")

    def test_add_and_list_students_and_criteria(self) -> None:
        self.seed()

        self.assertEqual(self.facade.list_students()[0].name, "Мария")
        self.assertEqual(self.facade.list_criteria()[0].name, "Практика")

    def test_duplicate_student_and_criterion_ids_are_rejected(self) -> None:
        self.seed()

        with self.assertRaises(DuplicateEntryError):
            self.facade.add_student("S-101", "Другая Мария")
        with self.assertRaises(DuplicateEntryError):
            self.facade.add_criterion("C-101", "Другая практика", "5", "1")

    def test_evaluation_requires_existing_student_and_criterion(self) -> None:
        self.seed()

        with self.assertRaises(EntityNotFoundError):
            self.facade.assign_evaluation("missing", "C-101", "8")
        with self.assertRaises(EntityNotFoundError):
            self.facade.assign_evaluation("S-101", "missing", "8")

    def test_assign_duplicate_update_and_cancel_evaluation(self) -> None:
        self.seed()
        self.facade.assign_evaluation("S-101", "C-101", "7")

        with self.assertRaises(DuplicateEntryError):
            self.facade.assign_evaluation("S-101", "C-101", "8")

        updated = self.facade.update_evaluation("S-101", "C-101", "9", "Исправлено")
        self.assertEqual(updated.score.value, Decimal("9"))
        self.assertEqual(self.facade.calculate_result("S-101").total_score, Decimal("9.00"))

        self.facade.cancel_evaluation("S-101", "C-101")
        self.assertIsNone(self.facade.calculate_result("S-101").total_score)
        with self.assertRaises(EvaluationNotFoundError):
            self.facade.cancel_evaluation("S-101", "C-101")

    def test_listing_evaluations_maps_criterion_names(self) -> None:
        self.seed()
        self.facade.assign_evaluation("S-101", "C-101", "8", "Сдано")

        view = self.facade.list_evaluations("S-101")[0]

        self.assertEqual(view.criterion_name, "Практика")
        self.assertEqual(view.score, Decimal("8"))
        self.assertEqual(view.max_score, Decimal("10"))
        self.assertEqual(view.comment, "Сдано")

    def test_calculation_strategy_is_injected_and_used(self) -> None:
        class FixedStrategy:
            def __init__(self) -> None:
                self.called = False

            def calculate(self, evaluations, criteria_by_id, max_total):
                self.called = True
                return Decimal("6.25")

        strategy = FixedStrategy()
        self.facade = PosFacade(
            students=InMemoryStudentRepository(),
            criteria=InMemoryCriterionRepository(),
            evaluations=InMemoryEvaluationRepository(),
            evaluation_factory=RubricEvaluationFactory(),
            result_calculator=StudentResultCalculator(strategy),
            result_exporter=self.exporter,
        )
        self.seed()
        self.facade.assign_evaluation("S-101", "C-101", "8")

        result = self.facade.calculate_result("S-101")

        self.assertTrue(strategy.called)
        self.assertEqual(result.total_score, Decimal("6.25"))

    def test_export_delegates_current_results_to_injected_exporter(self) -> None:
        self.seed()
        self.facade.assign_evaluation("S-101", "C-101", "8")

        result_path = self.facade.export_totals("out/results.csv")

        self.assertEqual(result_path, Path("out/results.csv"))
        self.assertEqual(self.exporter.results[0].total_score, Decimal("8.00"))
        self.assertEqual(self.exporter.destination, Path("out/results.csv"))


if __name__ == "__main__":
    unittest.main()
