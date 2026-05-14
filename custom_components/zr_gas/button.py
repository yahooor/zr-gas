"""Button platform for the 中燃在线 (ZR Gas) integration.

Provides a refresh button for each gas customer account, allowing users to
manually trigger data updates from the Home Assistant UI.
"""

from __future__ import annotations

import logging

from homeassistant.components.button import (
    AddEntitiesCallback,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZrGasCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

REFRESH_DESCRIPTION = ButtonEntityDescription(
    key="refresh",
    translation_key="refresh",
    icon="mdi:refresh",
)


class ZrGasRefreshButton(CoordinatorEntity[ZrGasCoordinator], ButtonEntity):
    """Button entity to manually refresh gas account data.

    Pressing this button triggers an immediate data refresh
    for the associated gas customer account.
    """

    def __init__(
        self,
        coordinator: ZrGasCoordinator,
        cust_code: str,
    ) -> None:
        """Initialize the button entity.

        Args:
            coordinator: Data update coordinator.
            cust_code: Customer code associated with this button.
        """
        super().__init__(coordinator)
        self._cust_code = cust_code
        self._attr_unique_id = f"zr_gas_{cust_code}_refresh"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cust_code)},
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._cust_code} Refresh"

    @property
    def translation_key(self) -> str:
        """Return translation key for the entity."""
        return REFRESH_DESCRIPTION.translation_key

    async def async_press(self) -> None:
        """Handle button press — trigger a data refresh."""
        _LOGGER.info("Manual refresh triggered for %s", self._cust_code)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform for each customer account.

    Args:
        hass: Home Assistant instance.
        entry: Config entry for the integration.
        async_add_entities: Callback to add entities.
    """
    coordinator: ZrGasCoordinator = entry.runtime_data
    cust_code = entry.data.get("cust_code", "unknown")

    entity = ZrGasRefreshButton(coordinator, cust_code)

    async_add_entities([entity])
    _LOGGER.info("Added refresh button for %s", cust_code)