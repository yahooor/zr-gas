"""中燃在线 Home Assistant 集成

版本: 1.0.7
作者: @yahooor

基于中燃在线平台抓包数据分析实现
"""

import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ZrGasApiClient, ZrGasApiError
from .const import DOMAIN, NAME, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button"]


class ZrGasCoordinator(DataUpdateCoordinator):
    """数据更新协调器"""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ):
        self._entry = entry
        self._api_client: Optional[ZrGasApiClient] = None
        self._scan_interval = scan_interval
        self._cached_data: Optional[Dict[str, Any]] = None  # 离线缓存

        super().__init__(
            hass,
            _LOGGER,
            name=NAME,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_setup(self) -> None:
        """初始化 API 客户端"""
        data = self._entry.data
        
        # 向下兼容：支持多种字段名
        token = data.get("token") or data.get("access_token") or data.get("accessToken")
        user_id = data.get("user_id") or data.get("userId") or data.get("USER_ID")
        cust_code = data.get("cust_code") or data.get("custCode") or data.get("CUST_CODE")

        if not token:
            _LOGGER.warning("未找到 Token，支持字段: token, access_token, accessToken")
            _LOGGER.debug("可用配置字段: %s", list(data.keys()))
            return

        session = aiohttp.ClientSession()
        self._api_client = ZrGasApiClient(session, token=token, user_id=user_id)
        _LOGGER.info(f"API客户端已初始化 (custCode: {cust_code})")

    async def _async_update_data(self) -> Dict[str, Any]:
        """更新数据"""
        if not self._api_client:
            await self._async_setup()

        if not self._api_client:
            raise UpdateFailed("API客户端未初始化")

        # 向下兼容：支持多种字段名
        cust_code = self._entry.data.get("cust_code") or self._entry.data.get("custCode") or self._entry.data.get("CUST_CODE")
        if not cust_code:
            raise UpdateFailed("未找到客户编号")

        try:
            # 获取燃气数据
            gas_data = await self._api_client.get_gas_data(cust_code)
            _LOGGER.debug(f"获取数据成功: {gas_data}")

            # 成功时更新缓存
            self._cached_data = gas_data
            return gas_data

        except Exception as e:
            _LOGGER.error(f"数据更新失败: {e}")
            # 网络失败时返回缓存数据
            if self._cached_data:
                _LOGGER.info("使用缓存数据")
                return self._cached_data
            raise UpdateFailed(f"数据更新失败: {e}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置配置条目"""
    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    coordinator = ZrGasCoordinator(
        hass=hass,
        entry=entry,
        scan_interval=scan_interval,
    )

    # 使用 entry.runtime_data 存储协调器 (HA 2024.1+ 现代写法)
    entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config_entry": entry,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(f"中燃在线集成已启动: {entry.title}")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        del hass.data[DOMAIN][entry.entry_id]

    _LOGGER.info(f"中燃在线集成已卸载: {entry.title}")
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """重新加载配置条目"""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
