"""Diagnostics support for the 中燃在线 (ZR Gas) integration.

Provides diagnostic data export for troubleshooting via Home Assistant's
device diagnostics feature (Settings > Devices > ⋮ > Download diagnostics).
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import ZrGasCoordinator
from .const import CONF_USER_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device: dict[str, Any],
) -> dict[str, Any]:
    """Return diagnostic data for a device.

    Args:
        hass: Home Assistant instance.
        entry: Config entry associated with the device.
        device: Device registry entry.

    Returns:
        Dictionary containing diagnostic data.
    """
    # Get config data with sensitive info redacted
    config_data = {
        **entry.data,
        "token": f"{entry.data.get('token', '')[:8]}***"
        if entry.data.get("token")
        else "",
        CONF_USER_ID: entry.data.get(CONF_USER_ID, ""),
    }

    # Get coordinator from entry.runtime_data
    coordinator: ZrGasCoordinator = entry.runtime_data
    cust_code = entry.data.get("cust_code", "unknown")

    if not coordinator:
        return {
            "entry": {
                "title": entry.title,
                "data": config_data,
                "options": entry.options,
                "version": entry.version,
                "minor_version": entry.minor_version,
            },
            "error": "Coordinator not found",
        }

    # Get coordinator status
    coordinator_data = {
        "name": coordinator.name,
        "last_update_success": coordinator.last_update_success,
        "update_interval": str(coordinator.update_interval)
        if coordinator.update_interval
        else None,
        "cust_code": cust_code,
    }

    # Get detailed data from coordinator
    data = coordinator.data if coordinator.data else {}
    data.update(coordinator_data)

    return {
        "entry": {
            "title": entry.title,
            "data": config_data,
            "options": entry.options,
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "coordinator": coordinator_data,
        "data": data,
    }