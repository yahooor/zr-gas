"""中燃在线集成 - 传感器实体

基于抓包数据的字段映射:
- oweMoney: 欠费金额
- qtyBalance: 账户余额
- lastRecord: 表读数
- qtyMeterBalance: 气量余额
- countMoney: 当月费用
- purchTimes: 购气次数
- lastRecordTime: 最后抄表时间
"""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, SENSOR_TYPES
from . import ZrGasCoordinator

_LOGGER = logging.getLogger(__name__)


class ZrGasSensor(CoordinatorEntity, SensorEntity):
    """中燃在线燃气传感器"""

    # API 字段映射（基于 HAR 抓包分析）
    FIELD_MAPPING = {
        # 余额/费用类
        "balance": "balance",  # 账户余额 (qtyBalance)
        "owed_amount": "owe_money",  # 欠费金额 (oweMoney)
        "new_owe_money": "new_owe_money",  # 最新欠费 (newOweMoney)
        "award_money": "award_money",  # 奖励金额
        "monthly_cost": "monthly_cost",  # 月度费用 (countMoney)
        "fee": "fee",  # 当前账单

        # 用量/气量类
        "monthly_usage": "monthly_usage",  # 月度用量
        "meter_reading": "meter_reading",  # 表读数 (lastRecord)
        "gas_balance": "gas_balance",  # 气量余额 (qtyMeterBalance)
        "max_gas": "max_gas",  # 最大购气量

        # 价格类
        "gas_price": "gas_price",  # 燃气单价

        # 次数/计数类
        "purch_times": "purch_times",  # 购气次数

        # 时间类
        "last_record_time": "last_record_time",  # 最后抄表时间

        # 信息类
        "card_type": "card_type",  # 卡类型
        "card_no": "card_no",  # 卡号
        "meter_type": "meter_type",  # 燃气表类型
        "meter_form_name": "meter_form_name",  # 燃气表型号
        "cust_status": "cust_status",  # 客户状态
        "cust_type": "cust_type",  # 客户类型
        "vent_date": "vent_date",  # 通气日期
        "bar_code": "bar_code",  # 表具条码
        "meter_loc": "meter_loc",  # 表具位置

        # === 与旧版 zr-gas-ha 兼容的传感器别名 ===
        "owe_money": "owe_money",  # 兼容旧版 owe_money 名称
        "purchase_count": "purch_times",  # 兼容旧版 purchase_count 名称
    }

    def __init__(
        self,
        coordinator: "ZrGasCoordinator",
        account_info: Dict[str, Any],
        sensor_type: str,
        entry: ConfigEntry,
    ):
        super().__init__(coordinator)
        self._account_info = account_info
        self._sensor_type = sensor_type
        self._entry = entry
        self._attr_has_entity_name = True

        sensor_config = SENSOR_TYPES.get(sensor_type, {})
        self._attr_name = sensor_config.get("name", sensor_type)
        self._attr_icon = sensor_config.get("icon", "mdi:help-circle")

        cust_code = account_info.get("custCode", account_info.get("cust_code", "default"))
        self._attr_unique_id = f"{DOMAIN}_{cust_code}_{sensor_type}"
        self._cust_code = cust_code

    @property
    def device_info(self) -> DeviceInfo:
        """设备信息"""
        return DeviceInfo(
            identifiers={(DOMAIN, self._cust_code)},
            name=f"{NAME} - {self._account_info.get('meterNo', self._cust_code)}",
            manufacturer="中国燃气",
            model="燃气表",
            sw_version="0.0.1",
            hw_version=self._account_info.get("meterNo", ""),
            suggested_area="燃气",
            configuration_url="https://mp.weixin.qq.com/",
        )

    @property
    def native_value(self) -> Optional[Any]:
        """获取传感器值"""
        if not self.coordinator.data:
            return None

        # 从 coordinator 数据中获取对应字段
        api_field = self.FIELD_MAPPING.get(self._sensor_type, self._sensor_type)
        value = self.coordinator.data.get(api_field)

        # 类型转换
        if value is None:
            return None

        if self._sensor_type == "last_record_time":
            return value  # 保持字符串格式

        if isinstance(value, (int, float)):
            return round(float(value), 2)

        return value

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """额外状态属性"""
        attrs = {}

        if self._account_info:
            attrs["meter_no"] = self._account_info.get("meterNo", "")
            attrs["address"] = self._account_info.get("address", "")
            attrs["cust_code"] = self._account_info.get("custCode", "")

        if self._sensor_type in ("balance", "owed_amount", "new_owe_money", "award_money", "monthly_cost", "fee", "gas_price"):
            attrs["currency"] = "CNY"

        elif self._sensor_type in ("monthly_usage", "meter_reading", "gas_balance"):
            attrs["unit_of_measurement"] = UnitOfVolume.CUBIC_METERS

        # 额外信息
        data = self.coordinator.data
        if data:
            attrs["comp_name"] = data.get("comp_name", "")
            attrs["cust_name"] = data.get("cust_name", "")
            attrs["mobile"] = data.get("mobile", "")

        return attrs

    @property
    def device_class(self) -> Optional[str]:
        """设备类"""
        sensor_config = SENSOR_TYPES.get(self._sensor_type, {})
        return sensor_config.get("device_class")

    @property
    def state_class(self) -> Optional[str]:
        """状态类"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """原生单位"""
        sensor_config = SENSOR_TYPES.get(self._sensor_type, {})
        unit = sensor_config.get("unit", "")

        if unit == "CNY":
            return "¥"
        elif unit == "m³":
            return UnitOfVolume.CUBIC_METERS

        return unit


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器实体"""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    account = entry.data.get("account", entry.data.get("cust_code", {}))

    # 传感器类型列表（基于 HAR 抓包分析，共22种）
    sensor_types = [
        # 余额/费用类
        "balance",         # 账户余额
        "owed_amount",      # 欠费金额
        "new_owe_money",    # 最新欠费
        "award_money",      # 奖励金额
        "monthly_cost",     # 月度费用
        "fee",             # 当前账单

        # 用量/气量类
        "monthly_usage",    # 月度用量
        "meter_reading",    # 表读数
        "gas_balance",      # 气量余额
        "max_gas",         # 最大购气量

        # 价格类
        "gas_price",        # 燃气单价

        # 次数/计数类
        "purch_times",      # 购气次数

        # 时间类
        "last_record_time", # 最后抄表日期

        # 信息类
        "card_type",        # 卡类型
        "card_no",          # 卡号
        "meter_type",       # 燃气表类型
        "meter_form_name",  # 燃气表型号
        "cust_status",      # 客户状态
        "cust_type",        # 客户类型
        "vent_date",        # 通气日期
        "bar_code",         # 表具条码
        "meter_loc",        # 表具位置

        # === 与旧版 zr-gas-ha 兼容的别名传感器 ===
        "purchase_count",   # 兼容旧版 (同 purch_times)
    ]

    sensors = []
    for sensor_type in sensor_types:
        sensor = ZrGasSensor(
            coordinator=coordinator,
            account_info=account,
            sensor_type=sensor_type,
            entry=entry,
        )
        sensors.append(sensor)

    # 添加诊断sensor
    diag_sensor = ZrGasDiagnosticSensor(
        coordinator=coordinator,
        account_info=account,
        entry=entry,
    )
    sensors.append(diag_sensor)

    async_add_entities(sensors, update_before_add=True)
    _LOGGER.info(f"已创建 {len(sensors)} 个中燃在线传感器")


class ZrGasDiagnosticSensor(CoordinatorEntity, SensorEntity):
    """诊断传感器 - 显示原始API数据"""

    def __init__(
        self,
        coordinator: "ZrGasCoordinator",
        account_info: Dict[str, Any],
        entry: ConfigEntry,
    ):
        super().__init__(coordinator)
        self._account_info = account_info
        self._entry = entry
        self._attr_has_entity_name = True
        self._attr_name = "诊断信息"
        self._attr_icon = "mdi:diagnostics"
        self._attr_unique_id = f"{DOMAIN}_diagnostic"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, "diagnostic")})

    @property
    def native_value(self) -> str:
        if self.coordinator.data:
            return "在线"
        return "离线"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        attrs = {}
        if self.coordinator.data:
            attrs["last_update"] = self.coordinator.data.get("last_update_time", "")
            attrs["cust_code"] = self.coordinator.data.get("cust_code", "")
        attrs["last_error"] = self.coordinator.last_update_error
        return attrs

    @property
    def device_class(self) -> Optional[str]:
        return "connectivity"
