import unittest

from vyshkat.main import ConsoleApp
from vyshkat.services import Fleet


class ScriptedInput:
    def __init__(self, values: list[str]) -> None:
        self._values = iter(values)

    def __call__(self, _prompt: str) -> str:
        return next(self._values)


class AlwaysAcceptInspection:
    def inspect(self, _transport) -> bool:
        return True


class RejectInspection:
    def inspect(self, _transport) -> bool:
        return False


class ConsoleAppTests(unittest.TestCase):
    def run_app(self, inputs: list[str], inspection_service) -> str:
        output: list[str] = []
        app = ConsoleApp(
            fleet=Fleet(inspection_service),
            input_fn=ScriptedInput(inputs),
            output_fn=output.append,
        )

        app.run()
        return "\n".join(output)

    def test_user_can_add_transport_and_item_then_read_reports(self) -> None:
        text = self.run_app(
            [
                "1",  # add transport
                "1",  # scooter
                "SAM-301",
                "1.5",
                "8",
                "да",
                "2",  # add item
                "1",  # helmet
                "HEL-301",
                "3",  # summary
                "4",  # beginner transports
                "5",  # inventory
                "0",
            ],
            AlwaysAcceptInspection(),
        )

        self.assertIn("Транспорт принят в парк", text)
        self.assertIn("Всего единиц: 2", text)
        self.assertIn("Суточное энергопотребление: 1.5 кВт·ч", text)
        self.assertIn("Самокат (SAM-301)", text)
        self.assertIn("Шлем (HEL-301)", text)

    def test_user_can_reject_transport_and_see_empty_report(self) -> None:
        text = self.run_app(
            [
                "1",
                "3",  # electric bicycle
                "EBI-302",
                "2",
                "7",
                "нет",
                "3",
                "0",
            ],
            RejectInspection(),
        )

        self.assertIn("Транспорт отклонён техосмотром", text)
        self.assertIn("Всего единиц: 0", text)
        self.assertIn("Суточное энергопотребление: 0 кВт·ч", text)


if __name__ == "__main__":
    unittest.main()
