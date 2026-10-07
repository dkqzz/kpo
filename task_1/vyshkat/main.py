"""Console demonstration of the VyshKat fleet application."""

from .domain import ChargingStation, ElectricBicycle, Helmet, Scooter
from .services import Fleet, ServiceCenter


def run_demo() -> None:
    fleet = Fleet(ServiceCenter())

    accepted_scooter = Scooter(
        "SAM-201", daily_energy_kwh=1.2, novice_score=8
    )
    rejected_bike = ElectricBicycle(
        "SAM-202",
        daily_energy_kwh=2.0,
        novice_score=7,
        ready_for_service=False,
    )

    accepted = fleet.add_transport(accepted_scooter)
    rejected = fleet.add_transport(rejected_bike)
    print("=== Приём техники ===")
    print(
        f"Техосмотр: {accepted_scooter.inventory_number} — "
        f"{'принято' if accepted else 'отклонено'}"
    )
    print(
        f"Техосмотр: {rejected_bike.inventory_number} — "
        f"{'принято' if rejected else 'отклонено'}"
    )

    fleet.add_item(Helmet("HEL-201"))
    fleet.add_item(ChargingStation("STA-201", daily_energy_kwh=3.8))

    print("\n=== Отчёты по парку ===")
    print(f"Всего единиц: {fleet.count}")
    print(f"Суточное энергопотребление: {fleet.daily_energy_kwh:.1f} кВт·ч")

    print("\nТехника для новичков:")
    for transport in fleet.beginner_transports():
        print(f"- {transport.name} ({transport.inventory_number})")

    print("\nВесь инвентарь:")
    for name, inventory_number in fleet.inventory_report():
        print(f"- {name} ({inventory_number})")


if __name__ == "__main__":
    run_demo()
