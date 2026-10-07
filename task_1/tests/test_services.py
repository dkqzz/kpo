import unittest

from vyshkat.domain import ChargingStation, Helmet, Scooter, Transport
from vyshkat.services import Fleet, ServiceCenter


class FakeInspectionService:
    def __init__(self, decision: bool) -> None:
        self.decision = decision
        self.inspected: list[Transport] = []

    def inspect(self, transport: Transport) -> bool:
        self.inspected.append(transport)
        return self.decision


class FleetServiceTests(unittest.TestCase):
    def test_injected_inspector_accepts_transport_and_records_call(self) -> None:
        inspector = FakeInspectionService(decision=True)
        fleet = Fleet(inspector)
        scooter = Scooter("SAM-100", daily_energy_kwh=1.2, novice_score=8)

        self.assertTrue(fleet.add_transport(scooter))
        self.assertEqual(inspector.inspected, [scooter])
        self.assertEqual(fleet.count, 1)

    def test_rejected_transport_is_not_added(self) -> None:
        fleet = Fleet(FakeInspectionService(decision=False))
        scooter = Scooter("SAM-101", daily_energy_kwh=1.2, novice_score=8)

        self.assertFalse(fleet.add_transport(scooter))
        self.assertEqual(fleet.count, 0)
        self.assertEqual(fleet.daily_energy_kwh, 0)
        self.assertEqual(fleet.inventory_report(), ())

    def test_service_center_uses_transport_readiness(self) -> None:
        service_center = ServiceCenter()
        ready = Scooter("SAM-102", daily_energy_kwh=1, novice_score=6)
        broken = Scooter(
            "SAM-103", daily_energy_kwh=1, novice_score=6, ready_for_service=False
        )

        self.assertTrue(service_center.inspect(ready))
        self.assertFalse(service_center.inspect(broken))

    def test_energy_total_includes_all_energy_consumers(self) -> None:
        fleet = Fleet(FakeInspectionService(decision=True))
        fleet.add_transport(Scooter("SAM-104", daily_energy_kwh=1.2, novice_score=8))
        fleet.add_item(ChargingStation("STA-100", daily_energy_kwh=3.3))
        fleet.add_item(Helmet("HEL-100"))

        self.assertAlmostEqual(fleet.daily_energy_kwh, 4.5)

    def test_empty_fleet_is_safe_to_query(self) -> None:
        fleet = Fleet(FakeInspectionService(decision=True))

        self.assertEqual(fleet.count, 0)
        self.assertEqual(fleet.daily_energy_kwh, 0)
        self.assertEqual(fleet.beginner_transports(), ())
        self.assertEqual(fleet.inventory_report(), ())

    def test_inventory_report_contains_transport_and_balance_items(self) -> None:
        fleet = Fleet(FakeInspectionService(decision=True))
        fleet.add_transport(Scooter("SAM-105", daily_energy_kwh=1, novice_score=7))
        fleet.add_item(Helmet("HEL-101"))
        fleet.add_item(ChargingStation("STA-101", daily_energy_kwh=2))

        self.assertEqual(
            fleet.inventory_report(),
            (
                ("Самокат", "SAM-105"),
                ("Шлем", "HEL-101"),
                ("Зарядная станция", "STA-101"),
            ),
        )

    def test_beginner_transports_include_only_accepted_suitable_transport(self) -> None:
        fleet = Fleet(FakeInspectionService(decision=True))
        beginner = Scooter("SAM-106", daily_energy_kwh=1, novice_score=6)
        experienced_only = Scooter("SAM-107", daily_energy_kwh=1, novice_score=5)
        fleet.add_transport(beginner)
        fleet.add_transport(experienced_only)

        self.assertEqual(fleet.beginner_transports(), (beginner,))


if __name__ == "__main__":
    unittest.main()
