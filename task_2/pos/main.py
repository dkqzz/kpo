"""Composition root for the POS console application."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from pos.application.facade import PosFacade
from pos.container import ApplicationContainer
from pos.presentation.console import ConsoleApp
from pos.presentation.demo import run_demo


def build_facade() -> PosFacade:
    """Compose the application graph and inject production adapters."""
    return ApplicationContainer().facade


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="ПОС — учёт оценок студентов")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="прогнать сквозной сценарий и экспортировать пример итогов",
    )
    parser.add_argument(
        "--export-path",
        type=Path,
        default=Path("results.csv"),
        help="путь к CSV-файлу в режиме --demo",
    )
    args = parser.parse_args(argv)
    facade = build_facade()
    if args.demo:
        run_demo(facade, export_path=args.export_path)
        return
    ConsoleApp(facade).run()


if __name__ == "__main__":
    main()
