import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from pos.domain.model import StudentResult
from pos.infrastructure.csv_exporter import CsvResultExporter
from pos.infrastructure.memory import (
    InMemoryCriterionRepository,
    InMemoryEvaluationRepository,
    InMemoryStudentRepository,
)
from pos.domain.errors import DuplicateEntryError, EntityNotFoundError, EvaluationNotFoundError
from pos.domain.factories import RubricEvaluationFactory
from pos.domain.model import AssessmentCriterion, Student


class InMemoryRepositoryTests(unittest.TestCase):
    def test_student_and_criterion_repositories_reject_duplicate_ids(self) -> None:
        students = InMemoryStudentRepository()
        criteria = InMemoryCriterionRepository()
        students.add(Student("S-201", "Олег"))
        criteria.add(AssessmentCriterion("C-201", "Зачёт", "10", "1"))

        with self.assertRaises(DuplicateEntryError):
            students.add(Student("S-201", "Другой Олег"))
        with self.assertRaises(DuplicateEntryError):
            criteria.add(AssessmentCriterion("C-201", "Другая работа", "5", "1"))
        with self.assertRaises(EntityNotFoundError):
            students.get("absent")

    def test_evaluation_repository_add_update_and_delete(self) -> None:
        student = Student("S-202", "Ирина")
        criterion = AssessmentCriterion("C-202", "Доклад", "10", "1")
        factory = RubricEvaluationFactory()
        repository = InMemoryEvaluationRepository()
        first = factory.create(student, criterion, "6")
        changed = factory.create(student, criterion, "9")
        repository.add(first)
        repository.update(changed)

        self.assertEqual(repository.get("S-202", "C-202").score.value, Decimal("9"))
        repository.delete("S-202", "C-202")
        self.assertEqual(repository.for_student("S-202"), ())
        with self.assertRaises(EvaluationNotFoundError):
            repository.delete("S-202", "C-202")


class CsvExporterTests(unittest.TestCase):
    def test_export_writes_russian_results_and_empty_totals(self) -> None:
        results = (
            StudentResult("S-301", "Елена", Decimal("8.25"), Decimal("10"), 2, 3),
            StudentResult("S-302", "Павел", None, Decimal("10"), 0, 3),
        )

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "results.csv"
            returned = CsvResultExporter().export(results, target)
            with target.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.reader(stream, delimiter=";"))

        self.assertEqual(returned, target)
        self.assertEqual(rows[1][1], "Елена")
        self.assertEqual(rows[1][2], "8,25")
        self.assertEqual(rows[1][4:], ["2", "3"])
        self.assertEqual(rows[2][1], "Павел")
        self.assertEqual(rows[2][2], "")


if __name__ == "__main__":
    unittest.main()
