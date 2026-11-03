import tempfile
import unittest
from pathlib import Path

from pos.application.facade import PosFacade
from pos.domain.factories import RubricEvaluationFactory
from pos.domain.services import StudentResultCalculator, WeightedAverageStrategy
from pos.infrastructure.csv_exporter import CsvResultExporter
from pos.infrastructure.memory import (
    InMemoryCriterionRepository,
    InMemoryEvaluationRepository,
    InMemoryStudentRepository,
)
from pos.presentation.console import ConsoleApp
from pos.presentation.demo import run_demo


class ScriptedInput:
    def __init__(self, values: list[str]) -> None:
        self._values = iter(values)

    def __call__(self, _prompt: str) -> str:
        return next(self._values)


def make_facade() -> PosFacade:
    return PosFacade(
        students=InMemoryStudentRepository(),
        criteria=InMemoryCriterionRepository(),
        evaluations=InMemoryEvaluationRepository(),
        evaluation_factory=RubricEvaluationFactory(),
        result_calculator=StudentResultCalculator(WeightedAverageStrategy()),
        result_exporter=CsvResultExporter(),
    )


class ConsoleApplicationTests(unittest.TestCase):
    def test_user_can_add_student_criterion_grade_calculate_and_export(self) -> None:
        output: list[str] = []
        with tempfile.TemporaryDirectory() as directory:
            export_path = Path(directory) / "results.csv"
            inputs = [
                "1", "S-401", "Надежда",
                "3", "C-401", "Практика", "10", "2",
                "5", "S-401", "C-401", "8", "Хорошо",
                "8", "S-401",
                "9", str(export_path),
                "0",
            ]
            ConsoleApp(make_facade(), ScriptedInput(inputs), output.append).run()

            self.assertTrue(export_path.exists())

        text = "\n".join(output)
        self.assertIn("Студент добавлен", text)
        self.assertIn("Критерий добавлен", text)
        self.assertIn("Оценка сохранена", text)
        self.assertIn("Текущий итог: 8.00/10", text)
        self.assertIn("Итоги экспортированы", text)

    def test_demo_runs_end_to_end_and_exports_totals(self) -> None:
        output: list[str] = []
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "demo.csv"

            run_demo(make_facade(), output.append, target)

            self.assertTrue(target.exists())

        text = "\n".join(output)
        self.assertIn("Демонстрация ПОС", text)
        self.assertIn("7.70/10", text)
        self.assertIn("9.40/10", text)
        self.assertIn("Экспорт завершён", text)


if __name__ == "__main__":
    unittest.main()
