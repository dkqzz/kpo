"""Interactive console interface for the VyshKat fleet application."""

from collections.abc import Callable

from .domain import (
    Bicycle,
    ChargingStation,
    ElectricBicycle,
    Helmet,
    Scooter,
    Transport,
)
from .services import Fleet, ServiceCenter


InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


class ConsoleApp:
    """Reads user commands and delegates business operations to ``Fleet``."""

    def __init__(
        self,
        fleet: Fleet,
        input_fn: InputFunction = input,
        output_fn: OutputFunction = print,
    ) -> None:
        self._fleet = fleet
        self._input = input_fn
        self._output = output_fn

    def run(self) -> None:
        while True:
            self._show_menu()
            command = self._input("Выберите действие: ").strip()

            if command == "0":
                self._output("Работа завершена.")
                return
            if command == "1":
                self._add_transport()
            elif command == "2":
                self._add_item()
            elif command == "3":
                self._show_summary()
            elif command == "4":
                self._show_beginner_transports()
            elif command == "5":
                self._show_inventory()
            else:
                self._output("Неизвестная команда. Выберите пункт от 0 до 5.")

    def _show_menu(self) -> None:
        self._output("\n=== ВышКат ===")
        self._output("1. Добавить транспорт")
        self._output("2. Добавить вещь")
        self._output("3. Показать отчёт по парку")
        self._output("4. Показать технику для новичков")
        self._output("5. Показать инвентарь")
        self._output("0. Выйти")

    def _add_transport(self) -> None:
        transport_types: dict[str, type[Transport]] = {
            "1": Scooter,
            "2": Bicycle,
            "3": ElectricBicycle,
        }
        transport_kind = self._read_choice(
            "Тип: 1 — самокат, 2 — велосипед, 3 — электровелосипед: ",
            transport_types,
        )
        inventory_number = self._read_non_empty("Инвентарный номер: ")
        daily_energy_kwh = self._read_non_negative_float(
            "Суточный расход энергии, кВт·ч: "
        )
        novice_score = self._read_int_in_range(
            "Простота для новичка (1–10): ", 1, 10
        )
        ready_for_service = self._read_yes_no("Техосмотр пройден? (да/нет): ")

        transport = transport_types[transport_kind](
            inventory_number=inventory_number,
            daily_energy_kwh=daily_energy_kwh,
            novice_score=novice_score,
            ready_for_service=ready_for_service,
        )
        if self._fleet.add_transport(transport):
            self._output("Транспорт принят в парк.")
        else:
            self._output("Транспорт отклонён техосмотром.")

    def _add_item(self) -> None:
        item_kind = self._read_choice(
            "Тип вещи: 1 — шлем, 2 — зарядная станция: ",
            {"1": Helmet, "2": ChargingStation},
        )
        inventory_number = self._read_non_empty("Инвентарный номер: ")

        if item_kind == "1":
            item = Helmet(inventory_number)
        else:
            daily_energy_kwh = self._read_non_negative_float(
                "Суточный расход энергии, кВт·ч: "
            )
            item = ChargingStation(inventory_number, daily_energy_kwh)

        self._fleet.add_item(item)
        self._output("Вещь добавлена на баланс.")

    def _show_summary(self) -> None:
        energy = format(self._fleet.daily_energy_kwh, "g")
        self._output(f"Всего единиц: {self._fleet.count}")
        self._output(f"Суточное энергопотребление: {energy} кВт·ч")

    def _show_beginner_transports(self) -> None:
        transports = self._fleet.beginner_transports()
        self._output("Техника для новичков:")
        if not transports:
            self._output("Нет подходящей техники.")
            return
        for transport in transports:
            self._output(f"- {transport.name} ({transport.inventory_number})")

    def _show_inventory(self) -> None:
        inventory = self._fleet.inventory_report()
        self._output("Весь инвентарь:")
        if not inventory:
            self._output("Инвентарь пуст.")
            return
        for name, inventory_number in inventory:
            self._output(f"- {name} ({inventory_number})")

    def _read_choice(self, prompt: str, options: dict[str, object]) -> str:
        while True:
            value = self._input(prompt).strip()
            if value in options:
                return value
            self._output("Некорректный выбор.")

    def _read_non_empty(self, prompt: str) -> str:
        while True:
            value = self._input(prompt).strip()
            if value:
                return value
            self._output("Значение не может быть пустым.")

    def _read_non_negative_float(self, prompt: str) -> float:
        while True:
            value = self._input(prompt).strip().replace(",", ".")
            try:
                number = float(value)
            except ValueError:
                self._output("Введите число.")
                continue
            if number >= 0:
                return number
            self._output("Число не может быть отрицательным.")

    def _read_int_in_range(self, prompt: str, minimum: int, maximum: int) -> int:
        while True:
            value = self._input(prompt).strip()
            try:
                number = int(value)
            except ValueError:
                self._output("Введите целое число.")
                continue
            if minimum <= number <= maximum:
                return number
            self._output(f"Введите число от {minimum} до {maximum}.")

    def _read_yes_no(self, prompt: str) -> bool:
        while True:
            value = self._input(prompt).strip().lower()
            if value in {"да", "д", "yes", "y"}:
                return True
            if value in {"нет", "н", "no", "n"}:
                return False
            self._output("Введите «да» или «нет».")


def main() -> None:
    app = ConsoleApp(Fleet(ServiceCenter()))
    app.run()


if __name__ == "__main__":
    main()
