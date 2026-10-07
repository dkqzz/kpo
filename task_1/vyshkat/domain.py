"""Core domain objects for the VyshKat fleet."""

from dataclasses import dataclass
from numbers import Real
from typing import Protocol, runtime_checkable


@runtime_checkable
class InventoryItem(Protocol):
    """An object that is tracked by an inventory number."""

    @property
    def name(self) -> str:
        ...

    @property
    def inventory_number(self) -> str:
        ...


@runtime_checkable
class EnergyConsumer(Protocol):
    """An object with a measurable daily energy consumption."""

    @property
    def daily_energy_kwh(self) -> float:
        ...


def _validate_inventory_number(inventory_number: object) -> None:
    if not isinstance(inventory_number, str) or not inventory_number.strip():
        raise ValueError("Инвентарный номер не может быть пустым")


def _validate_energy(daily_energy_kwh: object) -> None:
    if isinstance(daily_energy_kwh, bool) or not isinstance(daily_energy_kwh, Real):
        raise ValueError("Расход энергии должен быть числом")
    if daily_energy_kwh < 0:
        raise ValueError("Расход энергии не может быть отрицательным")


def _validate_novice_score(novice_score: object) -> None:
    if (
        not isinstance(novice_score, int)
        or isinstance(novice_score, bool)
        or not 1 <= novice_score <= 10
    ):
        raise ValueError("Простота для новичка должна быть от 1 до 10")


@dataclass(frozen=True)
class Transport:
    """Base type for transport that can be placed in the rental fleet."""

    inventory_number: str
    daily_energy_kwh: float
    novice_score: int
    ready_for_service: bool = True

    @property
    def name(self) -> str:
        return "Транспорт"

    def __post_init__(self) -> None:
        _validate_inventory_number(self.inventory_number)
        _validate_energy(self.daily_energy_kwh)
        _validate_novice_score(self.novice_score)

    @property
    def is_suitable_for_beginners(self) -> bool:
        return self.novice_score >= 6


@dataclass(frozen=True)
class Scooter(Transport):
    @property
    def name(self) -> str:
        return "Самокат"


@dataclass(frozen=True)
class Bicycle(Transport):
    @property
    def name(self) -> str:
        return "Велосипед"


@dataclass(frozen=True)
class ElectricBicycle(Transport):
    @property
    def name(self) -> str:
        return "Электровелосипед"


@dataclass(frozen=True)
class Helmet:
    inventory_number: str

    @property
    def name(self) -> str:
        return "Шлем"

    def __post_init__(self) -> None:
        _validate_inventory_number(self.inventory_number)


@dataclass(frozen=True)
class ChargingStation:
    inventory_number: str
    daily_energy_kwh: float

    @property
    def name(self) -> str:
        return "Зарядная станция"

    def __post_init__(self) -> None:
        _validate_inventory_number(self.inventory_number)
        _validate_energy(self.daily_energy_kwh)
