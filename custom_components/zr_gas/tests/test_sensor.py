"""Tests for ZrGasSensor (sensor.py)."""

import json
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.zr_gas.const import DOMAIN, SENSOR_TYPES
from custom_components.zr_gas.sensor import (
    ZrGasSensor,
    ZrGasDiagnosticSensor,
)


# === Helper Functions ===

def _create_sensor(sensor_type: str, data: Optional[Dict[str, Any]] = None) -> ZrGasSensor:
    """Create a ZrGasSensor for testing."""
    coordinator = MagicMock(spec=DataUpdateCoordinator)
    coordinator.data = data or {}
    coordinator.config_entry = MagicMock()
    coordinator.last_update_error = None
    
    account_info = {"custCode": "CUST001", "meterNo": "METER001"}
    entry = MagicMock()
    entry.data = {"account": account_info}
    
    sensor = ZrGasSensor(coordinator, account_info, sensor_type, entry)
    return sensor


# === Test Classes ===

class TestZrGasSensorInit:
    """Test ZrGasSensor initialization."""

    def test_init_balance(self):
        """Test initialization for balance sensor."""
        sensor = _create_sensor("balance")
        
        assert sensor._sensor_type == "balance"
        assert sensor._attr_has_entity_name is True
        assert "balance" in sensor._attr_unique_id
        assert sensor._attr_icon == "mdi:currency-cny"

    def test_init_meter_reading(self):
        """Test initialization for meter_reading sensor."""
        sensor = _create_sensor("meter_reading")
        
        assert sensor._sensor_type == "meter_reading"
        assert sensor._attr_icon == "mdi:gauge"

    def test_init_with_account_info(self):
        """Test initialization with account info."""
        coordinator = MagicMock()
        coordinator.data = {}
        account_info = {"custCode": "TEST_CODE", "meterNo": "TEST_METER"}
        entry = MagicMock()
        entry.data = {"account": account_info}
        
        sensor = ZrGasSensor(coordinator, account_info, "balance", entry)
        
        assert sensor._cust_code == "TEST_CODE"
        assert "TEST_CODE" in sensor._attr_unique_id

    def test_init_unique_id_format(self):
        """Test unique_id format."""
        sensor = _create_sensor("balance")
        
        assert sensor._attr_unique_id.startswith(f"{DOMAIN}_")
        assert "CUST001" in sensor._attr_unique_id
        assert sensor._attr_unique_id.endswith("_balance")


class TestNativeValue:
    """Test native_value property."""

    def test_native_value_with_data(self):
        """Test native_value returns correct value."""
        data = {"balance": 100.50}
        sensor = _create_sensor("balance", data)
        
        assert sensor.native_value == 100.50

    def test_native_value_none_data(self):
        """Test native_value with None coordinator data."""
        sensor = _create_sensor("balance", None)
        sensor.coordinator.data = None
        
        assert sensor.native_value is None

    def test_native_value_field_not_found(self):
        """Test native_value when field not in coordinator data."""
        data = {"other_field": 123}
        sensor = _create_sensor("balance", data)
        
        # balance maps to "balance" key in data
        assert sensor.native_value is None

    def test_native_value_last_record_time(self):
        """Test native_value for last_record_time (returns string)."""
        data = {"last_record_time": "2026-05-01 10:30:00"}
        sensor = _create_sensor("last_record_time", data)
        
        assert sensor.native_value == "2026-05-01 10:30:00"
        # Should not be rounded
        assert isinstance(sensor.native_value, str)

    def test_native_value_float(self):
        """Test native_value rounds float values."""
        data = {"balance": 100.5678}
        sensor = _create_sensor("balance", data)
        
        assert sensor.native_value == pytest.approx(100.57, 0.01)

    def test_native_value_int(self):
        """Test native_value rounds int values."""
        data = {"purch_times": 5}
        sensor = _create_sensor("purch_times", data)
        
        assert sensor.native_value == 5.0

    def test_native_value_zero(self):
        """Test native_value with zero."""
        data = {"balance": 0.0}
        sensor = _create_sensor("balance", data)
        
        assert sensor.native_value == 0.0

    def test_native_value_negative(self):
        """Test native_value with negative (owed amount)."""
        data = {"owe_money": -50.0}
        sensor = _create_sensor("owed_amount", data)
        
        assert sensor.native_value == -50.0


class TestExtraStateAttributes:
    """Test extra_state_attributes property."""

    def test_extra_state_attributes_monetary(self):
        """Test attributes for monetary sensors."""
        data = {"last_update_time": "2026-05-14T10:30:00"}
        account_info = {"custCode": "CUST001", "meterNo": "METER001", "address": "Test Address"}
        sensor = _create_sensor("balance", data)
        
        attrs = sensor.extra_state_attributes
        
        assert attrs["currency"] == "CNY"
        assert "meter_no" in attrs
        assert "address" in attrs

    def test_extra_state_attributes_gas(self):
        """Test attributes for gas sensors."""
        data = {}
        sensor = _create_sensor("meter_reading", data)
        
        attrs = sensor.extra_state_attributes
        
        assert attrs["unit_of_measurement"] == UnitOfVolume.CUBIC_METERS

    def test_extra_state_attributes_info(self):
        """Test attributes include cust_info."""
        data = {
            "comp_name": "Test Company",
            "cust_name": "Test User",
            "mobile": "13800138000",
        }
        sensor = _create_sensor("card_type", data)
        
        attrs = sensor.extra_state_attributes
        
        assert attrs["comp_name"] == "Test Company"
        assert attrs["cust_name"] == "Test User"
        assert attrs["mobile"] == "13800138000"


class TestDeviceInfo:
    """Test device_info property."""

    def test_device_info(self):
        """Test device_info returns correct structure."""
        sensor = _create_sensor("balance")
        
        info = sensor.device_info
        
        assert DOMAIN in info["identifiers"]
        assert "中国燃气" in info["manufacturer"]
        assert info["suggested_area"] == "燃气"


class TestDeviceClass:
    """Test device_class property."""

    def test_device_class_monetary(self):
        """Test device_class for monetary sensors."""
        sensor = _create_sensor("balance")
        
        assert sensor.device_class == "monetary"

    def test_device_class_gas(self):
        """Test device_class for gas sensors."""
        sensor = _create_sensor("meter_reading")
        
        assert sensor.device_class == "gas"

    def test_device_class_none(self):
        """Test device_class for sensors without device class."""
        sensor = _create_sensor("card_type")
        
        assert sensor.device_class is None


class TestStateClass:
    """Test state_class property."""

    def test_state_class(self):
        """Test state_class returns MEASUREMENT."""
        sensor = _create_sensor("balance")
        
        assert sensor.state_class == "measurement"


class TestNativeUnitOfMeasurement:
    """Test native_unit_of_measurement property."""

    def test_native_unit_monetary(self):
        """Test unit for monetary sensors."""
        sensor = _create_sensor("balance")
        
        assert sensor.native_unit_of_measurement == "¥"

    def test_native_unit_gas(self):
        """Test unit for gas sensors."""
        sensor = _create_sensor("meter_reading")
        
        assert sensor.native_unit_of_measurement == UnitOfVolume.CUBIC_METERS

    def test_native_unit_none(self):
        """Test unit for sensors without unit."""
        sensor = _create_sensor("card_type")
        
        assert sensor.native_unit_of_measurement is None


class TestSensorTypesConsistency:
    """Test sensor types consistency."""

    def test_all_sensor_types_in_field_mapping(self):
        """Test all SENSOR_TYPES have FIELD_MAPPING."""
        sensor = _create_sensor("balance")
        
        for sensor_type in SENSOR_TYPES.keys():
            assert sensor_type in sensor.FIELD_MAPPING, f"{sensor_type} not in FIELD_MAPPING"

    def test_field_mapping_values_in_get_gas_data(self):
        """Test FIELD_MAPPING values match get_gas_data keys."""
        # This is a static check - get_gas_data should return keys matching FIELD_MAPPING values
        sensor = _create_sensor("balance")
        
        expected_keys = {
            "balance", "owe_money", "new_owe_money", "award_money",
            "monthly_cost", "fee", "meter_reading", "gas_balance",
            "max_gas", "gas_price", "monthly_usage", "purch_times",
            "last_record_time", "card_type", "card_no", "meter_type",
            "meter_form_name", "cust_status", "cust_type", "vent_date",
            "bar_code", "meter_loc",
        }
        
        for mapping_value in sensor.FIELD_MAPPING.values():
            assert mapping_value in expected_keys or mapping_value == "purchase_count"


class TestZrGasDiagnosticSensor:
    """Test ZrGasDiagnosticSensor."""

    def test_init(self):
        """Test diagnostic sensor initialization."""
        coordinator = MagicMock()
        coordinator.data = {"cust_code": "CUST001"}
        coordinator.last_update_error = None
        account_info = {}
        entry = MagicMock()
        
        diag = ZrGasDiagnosticSensor(coordinator, account_info, entry)
        
        assert diag._attr_name == "诊断信息"
        assert diag._attr_icon == "mdi:diagnostics"

    def test_native_value_online(self):
        """Test native_value when online."""
        coordinator = MagicMock()
        coordinator.data = {"cust_code": "CUST001"}
        account_info = {}
        entry = MagicMock()
        
        diag = ZrGasDiagnosticSensor(coordinator, account_info, entry)
        
        assert diag.native_value == "在线"

    def test_native_value_offline(self):
        """Test native_value when offline."""
        coordinator = MagicMock()
        coordinator.data = None
        account_info = {}
        entry = MagicMock()
        
        diag = ZrGasDiagnosticSensor(coordinator, account_info, entry)
        
        assert diag.native_value == "离线"

    def test_extra_state_attributes(self):
        """Test diagnostic sensor attributes."""
        coordinator = MagicMock()
        coordinator.data = {"cust_code": "CUST001", "last_update_time": "2026-05-14T10:30:00"}
        coordinator.last_update_error = "Previous error"
        account_info = {}
        entry = MagicMock()
        
        diag = ZrGasDiagnosticSensor(coordinator, account_info, entry)
        attrs = diag.extra_state_attributes
        
        assert attrs["last_error"] == "Previous error"
        assert attrs["cust_code"] == "CUST001"
