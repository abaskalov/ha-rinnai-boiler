"""Мастер настройки интеграции Rinnai."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .api import RinnaiApi, RinnaiAuthError, RinnaiError
from .const import CONF_DEVICE_ID, CONF_ROOM_CONTROL_ID, DOMAIN

_MAC_RE = re.compile(r"^[0-9a-f]{12}$")
_UUID_RE = re.compile(
    r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$"
)


class RinnaiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Спрашивает идентификатор пульта и проверяет связь."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            room_control_id = (
                user_input[CONF_ROOM_CONTROL_ID].strip().lower().replace(":", "").replace("-", "")
            )
            device_id = user_input[CONF_DEVICE_ID].strip().upper()
            if not _MAC_RE.match(room_control_id):
                errors[CONF_ROOM_CONTROL_ID] = "invalid_id"
            elif not _UUID_RE.match(device_id):
                errors[CONF_DEVICE_ID] = "invalid_device_id"
            else:
                await self.async_set_unique_id(room_control_id)
                self._abort_if_unique_id_configured()

                api = RinnaiApi(room_control_id, device_id)
                try:
                    await self.hass.async_add_executor_job(api.get_status)
                except RinnaiAuthError:
                    errors["base"] = "invalid_room_control_id"
                except RinnaiError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title="Газовый котёл Rinnai",
                        data={
                            CONF_ROOM_CONTROL_ID: room_control_id,
                            CONF_DEVICE_ID: device_id,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ROOM_CONTROL_ID,
                        default=(user_input or {}).get(CONF_ROOM_CONTROL_ID, ""),
                    ): str,
                    vol.Required(
                        CONF_DEVICE_ID,
                        default=(user_input or {}).get(CONF_DEVICE_ID, ""),
                    ): str,
                }
            ),
            errors=errors,
        )
