"""CSV result-export adapter kept outside the domain model."""

import csv
from collections.abc import Sequence
from pathlib import Path

from pos.domain.model import StudentResult


def _decimal_for_csv(value) -> str:
    return format(value, ".2f").replace(".", ",")


class CsvResultExporter:
    """Export course totals using UTF-8 BOM and a semicolon delimiter."""

    def export(
        self, results: Sequence[StudentResult], destination: str | Path
    ) -> Path:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow(
                (
                    "ID студента",
                    "Студент",
                    "Итог",
                    "Максимум",
                    "Оценено критериев",
                    "Всего критериев",
                )
            )
            for result in results:
                writer.writerow(
                    (
                        result.student_id,
                        result.student_name,
                        "" if result.total_score is None else _decimal_for_csv(result.total_score),
                        _decimal_for_csv(result.max_total),
                        result.graded_criteria,
                        result.total_criteria,
                    )
                )
        return path
