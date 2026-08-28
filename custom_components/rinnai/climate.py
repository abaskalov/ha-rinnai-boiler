"""Отопление котла Rinnai (термостат, виден в Apple Home)."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity, ClimateEntityFeature, HVACAction, HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RinnaiConfigEntry
from .const import (
    FLAG_CIRCUIT_MODE, FLAG_HEATING, FLAG_HOT_WATER, FLAG_POWER, ROOM_MAX, ROOM_MIN,
)
from .entity import RinnaiEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RinnaiConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RinnaiClimate(entry.runtime_data)])


class RinnaiClimate(RinnaiEntity, ClimateEntity):
    """Отопление по температуре воздуха в помещении."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_min_temp = ROOM_MIN
    _attr_max_temp = ROOM_MAX
    _attr_target_temperature_step = 1

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "climate", "Отопление")

    @property
    def current_temperature(self) -> float | None:
        return self._data.get("room_cur")

    @property
    def target_temperature(self) -> float | None:
        value = self._data.get("room_set")
        if value is None:
            return None
        # В режиме «по теплоносителю» пульт кладёт в это поле уставку контура,
        # которая выходит за диапазон комнатного термостата. Показываем
        # значение, ограниченное допустимым диапазоном, иначе Home Assistant
        # и HomeKit получают состояние вне собственных границ сущности.
        return min(max(float(value), ROOM_MIN), ROOM_MAX)

    @property
    def extra_state_attributes(self) -> dict:
        return {"raw_room_setpoint": self._data.get("room_set")}

    @property
    def hvac_mode(self) -> HVACMode:
        data = self._data
        return HVACMode.HEAT if data.get("power") and data.get("heating") else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        data = self._data
        if not data.get("power") or not data.get("heating"):
            return HVACAction.OFF
        current, target = data.get("room_cur"), data.get("room_set")
        if current is not None and target is not None and current < target:
            return HVACAction.HEATING
        return HVACAction.IDLE

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        value = max(ROOM_MIN, min(ROOM_MAX, int(round(temperature))))
        await self.coordinator.async_set_room_temp(value)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        data = self._data
        flags = FLAG_POWER
        if data.get("circuit_mode"):
            flags |= FLAG_CIRCUIT_MODE
        if data.get("hot_water"):
            flags |= FLAG_HOT_WATER
        if hvac_mode == HVACMode.HEAT:
            flags |= FLAG_HEATING
        await self.coordinator.async_set_flags(flags)

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)
