"""Repeatable end-to-end console scenario required by the assignment."""

from collections.abc import Callable
from pathlib import Path

from pos.application.facade import PosFacade


OutputFunction = Callable[[str], None]


def run_demo(
    facade: PosFacade,
    output_fn: OutputFunction = print,
    export_path: str | Path = "results.csv",
) -> None:
    output_fn("Демонстрация ПОС: добавление студентов, критериев и оценок.")
    facade.add_student("S-001", "Иванов Иван")
    facade.add_student("S-002", "Петров Петр")
    facade.add_criterion("C-001", "Практическая работа", "10", "2")
    facade.add_criterion("C-002", "Защита проекта", "20", "3")
    facade.assign_evaluation("S-001", "C-001", "8")
    facade.assign_evaluation("S-001", "C-002", "15")
    facade.assign_evaluation("S-002", "C-001", "10")
    facade.assign_evaluation("S-002", "C-002", "18")

    output_fn("Текущие итоги:")
    for result in facade.calculate_all_results():
        total = "не рассчитан" if result.total_score is None else f"{result.total_score:.2f}/10"
        output_fn(f"- {result.student_name}: {total}")
    exported = facade.export_totals(export_path)
    output_fn(f"Экспорт завершён: {exported}")
