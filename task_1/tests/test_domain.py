import unittest
from dataclasses import dataclass

from vyshkat.domain import (
    Bicycle,
    ChargingStation,
    ElectricBicycle,
    EnergyConsumer,
    Helmet,
    InventoryItem,
    Scooter,
    Transport,
)


class DomainModelTests(unittest.TestCase):
    def test_capability_protocols_describe_read_only_attributes(self) -> None:
        self.assertIsInstance(InventoryItem.__dict__["name"], property)
        self.assertIsInstance(InventoryItem.__dict__["inventory_number"], property)
        self.assertIsInstance(EnergyConsumer.__dict__["daily_energy_kwh"], property)

    def test_inventory_implementations_expose_name_as_instance_property(self) -> None:
        self.assertIsInstance(Scooter.name, property)
        self.assertIsInstance(Helmet.name, property)
        self.assertIsInstance(ChargingStation.name, property)

    def test_concrete_objects_expose_required_capabilities(self) -> None:
        scooter = Scooter("SAM-001", daily_energy_kwh=1.2, novice_score=8)
        station = ChargingStation("STA-001", daily_energy_kwh=4.5)
        bicycle = Bicycle("BIK-001", daily_energy_kwh=0, novice_score=7)
        electric_bicycle = ElectricBicycle(
            "EBI-001", daily_energy_kwh=1.8, novice_score=6
        )
        helmet = Helmet("HEL-001")

        self.assertEqual(scooter.name, "Самокат")
        self.assertEqual(station.name, "Зарядная станция")
        self.assertEqual(bicycle.name, "Велосипед")
        self.assertEqual(electric_bicycle.name, "Электровелосипед")
        self.assertEqual(helmet.name, "Шлем")
        self.assertIsInstance(scooter, InventoryItem)
        self.assertIsInstance(station, EnergyConsumer)
        self.assertEqual(scooter.inventory_number, "SAM-001")
        self.assertEqual(station.daily_energy_kwh, 4.5)

    def test_only_score_at_least_six_is_beginner_friendly(self) -> None:
        almost_ready = Scooter("SAM-005", daily_energy_kwh=1, novice_score=5)
        boundary = Scooter("SAM-006", daily_energy_kwh=1, novice_score=6)

        self.assertFalse(almost_ready.is_suitable_for_beginners)
        self.assertTrue(boundary.is_suitable_for_beginners)

    def test_new_transport_subclass_uses_existing_domain_behavior(self) -> None:
        @dataclass(frozen=True)
        class CargoBike(Transport):
            @property
            def name(self) -> str:
                return "Грузовой велосипед"

        cargo_bike = CargoBike("CAR-001", daily_energy_kwh=0, novice_score=7)

        self.assertEqual(cargo_bike.name, "Грузовой велосипед")
        self.assertTrue(cargo_bike.is_suitable_for_beginners)

    def test_invalid_inventory_number_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Helmet("   ")

    def test_negative_energy_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ChargingStation("STA-002", daily_energy_kwh=-1)

    def test_novice_score_outside_one_to_ten_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Scooter("SAM-010", daily_energy_kwh=1, novice_score=11)


if __name__ == "__main__":
    unittest.main()
