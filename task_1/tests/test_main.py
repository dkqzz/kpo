import unittest
from contextlib import redirect_stdout
from io import StringIO

from vyshkat.main import run_demo


class ConsoleDemoTests(unittest.TestCase):
    def test_demo_prints_all_required_scenarios(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            run_demo()

        text = output.getvalue()
        expected_fragments = (
            "Техосмотр: SAM-201 — принято",
            "Техосмотр: SAM-202 — отклонено",
            "Всего единиц: 3",
            "Суточное энергопотребление: 5.0 кВт·ч",
            "Самокат (SAM-201)",
            "Шлем (HEL-201)",
            "Зарядная станция (STA-201)",
        )

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
