"""Application services for accepting and reporting on fleet items."""

from typing import Protocol, runtime_checkable

from .domain import EnergyConsumer, InventoryItem, Transport


@runtime_checkable
class InspectionService(Protocol):
    """Dependency used by the fleet to decide whether transport is accepted."""

    def inspect(self, transport: Transport) -> bool:
        ...


class ServiceCenter:
    """Production inspection service for the demonstration application."""

    def inspect(self, transport: Transport) -> bool:
        return transport.ready_for_service


class Fleet:
    """Stores accepted transport and balance items and answers fleet queries."""

    def __init__(self, inspection_service: InspectionService) -> None:
        self._inspection_service = inspection_service
        self._items: list[InventoryItem] = []

    def add_transport(self, transport: Transport) -> bool:
        if not self._inspection_service.inspect(transport):
            return False
        self._items.append(transport)
        return True

    def add_item(self, item: InventoryItem) -> None:
        self._items.append(item)

    @property
    def count(self) -> int:
        return len(self._items)

    @property
    def daily_energy_kwh(self) -> float:
        return sum(
            item.daily_energy_kwh
            for item in self._items
            if isinstance(item, EnergyConsumer)
        )

    def beginner_transports(self) -> tuple[Transport, ...]:
        return tuple(
            item
            for item in self._items
            if isinstance(item, Transport) and item.is_suitable_for_beginners
        )

    def inventory_report(self) -> tuple[tuple[str, str], ...]:
        return tuple((item.name, item.inventory_number) for item in self._items)
