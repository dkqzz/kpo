"""Interactive console interface for the assessment application."""

from collections.abc import Callable
from decimal import Decimal, InvalidOperation

from pos.application.facade import PosFacade
from pos.domain.errors import PosError


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


class ConsoleApp:
    """Reads commands and delegates all business operations to ``PosFacade``."""

    def __init__(
        self,
        facade: PosFacade,
        input_fn: InputFunction = input,
        output_fn: OutputFunction = print,
    ) -> None:
        self._facade = facade
        self._input = input_fn
        self._output = output_fn

    def run(self) -> None:
        while True:
            self._show_menu()
            command = self._input("Выберите действие: ").strip()
            if command == "0":
                self._output("Работа завершена.")
                return
            try:
                self._dispatch(command)
            except (PosError, OSError) as exc:
                self._output(f"Ошибка: {exc}")

    def _dispatch(self, command: str) -> None:
        actions = {
            "1": self._add_student,
            "2": self._show_students,
            "3": self._add_criterion,
            "4": self._show_criteria,
            "5": lambda: self._save_evaluation(update=False),
            "6": lambda: self._save_evaluation(update=True),
            "7": self._cancel_evaluation,
            "8": self._show_student_result,
            "9": self._export_results,
        }
        action = actions.get(command)
        if action is None:
            self._output("Неизвестная команда. Выберите пункт от 0 до 9.")
            return
        action()

    def _show_menu(self) -> None:
        self._output("\n=== ПОС: оценки студентов ===")
        self._output("1. Добавить студента")
        self._output("2. Показать студентов")
        self._output("3. Добавить критерий рубрикатора")
        self._output("4. Показать рубрикатор")
        self._output("5. Выставить оценку")
        self._output("6. Исправить оценку")
        self._output("7. Отменить оценку")
        self._output("8. Показать оценки и текущий итог студента")
        self._output("9. Экспортировать итоги в CSV")
        self._output("0. Выйти")

    def _add_student(self) -> None:
        student = self._facade.add_student(
            self._read_non_empty("ID студента: "),
            self._read_non_empty("Имя студента: "),
        )
        self._output(f"Студент добавлен: {student.name} ({student.student_id}).")

    def _show_students(self) -> None:
        students = self._facade.list_students()
        self._output("Студенты:")
        if not students:
            self._output("Список студентов пуст.")
            return
        for student in students:
            self._output(f"- {student.name} ({student.student_id})")

    def _add_criterion(self) -> None:
        criterion = self._facade.add_criterion(
            criterion_id=self._read_non_empty("ID критерия: "),
            name=self._read_non_empty("Название критерия: "),
            max_score=self._read_decimal("Максимальный балл: "),
            weight=self._read_decimal("Вес критерия: "),
        )
        self._output(f"Критерий добавлен: {criterion.name} ({criterion.criterion_id}).")

    def _show_criteria(self) -> None:
        criteria = self._facade.list_criteria()
        self._output("Рубрикатор:")
        if not criteria:
            self._output("Критериев пока нет.")
            return
        for criterion in criteria:
            self._output(
                f"- {criterion.name} ({criterion.criterion_id}): "
                f"максимум {format(criterion.max_score, 'f')}, "
                f"вес {format(criterion.weight, 'f')}"
            )

    def _save_evaluation(self, update: bool) -> None:
        student_id = self._read_non_empty("ID студента: ")
        criterion_id = self._read_non_empty("ID критерия: ")
        score = self._read_decimal("Балл: ")
        comment = self._input("Комментарий (необязательно): ").strip()
        if update:
            self._facade.update_evaluation(student_id, criterion_id, score, comment)
            self._output("Оценка исправлена.")
        else:
            self._facade.assign_evaluation(student_id, criterion_id, score, comment)
            self._output("Оценка сохранена.")

    def _cancel_evaluation(self) -> None:
        student_id = self._read_non_empty("ID студента: ")
        criterion_id = self._read_non_empty("ID критерия: ")
        self._facade.cancel_evaluation(student_id, criterion_id)
        self._output("Оценка отменена.")

    def _show_student_result(self) -> None:
        student_id = self._read_non_empty("ID студента: ")
        evaluations = self._facade.list_evaluations(student_id)
        result = self._facade.calculate_result(student_id)
        self._output(f"Оценки студента {result.student_name}:")
        if not evaluations:
            self._output("Оценок пока нет.")
        else:
            for evaluation in evaluations:
                line = (
                    f"- {evaluation.criterion_name}: "
                    f"{format(evaluation.score, 'f')}/"
                    f"{format(evaluation.max_score, 'f')}"
                )
                if evaluation.comment:
                    line += f" — {evaluation.comment}"
                self._output(line)
        if result.total_score is None:
            self._output("Текущий итог пока не рассчитан: нет оценок.")
        else:
            self._output(
                f"Текущий итог: {result.total_score:.2f}/{result.max_total:.0f} "
                f"(оценено критериев: {result.graded_criteria}/{result.total_criteria})."
            )

    def _export_results(self) -> None:
        destination = self._input("Путь к CSV (Enter — results.csv): ").strip()
        path = self._facade.export_totals(destination or "results.csv")
        self._output(f"Итоги экспортированы: {path}")

    def _read_non_empty(self, prompt: str) -> str:
        while True:
            value = self._input(prompt).strip()
            if value:
                return value
            self._output("Значение не может быть пустым.")

    def _read_decimal(self, prompt: str) -> Decimal:
        while True:
            value = self._input(prompt).strip().replace(",", ".")
            try:
                number = Decimal(value)
            except InvalidOperation:
                self._output("Введите число.")
                continue
            if not number.is_finite():
                self._output("Введите конечное число.")
                continue
            return number
