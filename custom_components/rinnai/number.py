"""Уставка температуры теплоносителя."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RinnaiConfigEntry
from .const import CIRCUIT_MAX, CIRCUIT_MIN
from .entity import RinnaiEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RinnaiConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RinnaiCircuitTemperature(entry.runtime_data)])


class RinnaiCircuitTemperature(RinnaiEntity, NumberEntity):
    """Температура воды в контуре отопления (CMD 03)."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_min_value = CIRCUIT_MIN
    _attr_native_max_value = CIRCUIT_MAX
    _attr_native_step = 1

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "circuit_temp", "Теплоноситель")

    @property
    def native_value(self) -> float | None:
        return self._data.get("circuit_set")

    async def async_set_native_value(self, value: float) -> None:
        temperature = max(CIRCUIT_MIN, min(CIRCUIT_MAX, int(round(value))))
        await self.coordinator.async_set_circuit_temp(temperature)
