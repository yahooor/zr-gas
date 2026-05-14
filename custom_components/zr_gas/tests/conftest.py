"""Pytest fixtures for zr_gas integration tests."""

import json
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.zr_gas.const import DOMAIN, VERSION
from custom_components.zr_gas.api import ZrGasApiClient, ZrGasApiError


# === Mock Data Fixtures ===

@pytest.fixture
def mock_cust_info() -> Dict[str, Any]:
    """Mock customer info from API."""
    return {
        "custCode": "CUST001",
        "custName": "张三",
        "meterNo": "METER001",
        "address": "测试地址",
        "mobile": "13800138000",
        "qtyBalance": 100.50,
        "oweMoney": 0.0,
        "newOweMoney": 0.0,
        "awardMoney": 5.0,
        "countMoney": 50.0,
        "fee": 50.0,
        "lastRecord": 12345.6,
        "qtyMeterBalance": 50.5,
        "maxGas": 500.0,
        "price": 2.99,
        "purchTimes": 5,
        "lastRecordTime": "2026-05-01 10:30:00",
        "cardType": "IC卡",
        "cardNo": "1234567890123456",
        "metertype": "智能表",
        "meterFormName": "G2.5",
        "custStatus": "正常",
        "custType": "居民",
        "compName": "测试燃气公司",
    }


@pytest.fixture
def mock_meter_info() -> Dict[str, Any]:
    """Mock meter info from API."""
    return {
        "cardType": "IC卡",
        "cardNo": "1234567890123456",
        "meterType": "智能表",
        "meterFormName": "G2.5",
        "ventDate": "2020-01-01",
        "barCode": "BC001",
        "meterloc": "厨房",
    }


@pytest.fixture
def mock_gas_data() -> Dict[str, Any]:
    """Mock gas data returned by get_gas_data()."""
    return {
        "cust_code": "CUST001",
        "cust_name": "张三",
        "meter_no": "METER001",
        "address": "测试地址",
        "mobile": "13800138000",
        "balance": 100.50,
        "owe_money": 0.0,
        "new_owe_money": 0.0,
        "award_money": 5.0,
        "monthly_cost": 50.0,
        "fee": 50.0,
        "meter_reading": 12345.6,
        "gas_balance": 50.5,
        "max_gas": 500.0,
        "monthly_usage": 10.5,
        "gas_price": 2.99,
        "purch_times": 5,
        "last_record_time": "2026-05-01 10:30:00",
        "card_type": "IC卡",
        "card_no": "1234567890123456",
        "meter_type": "智能表",
        "meter_form_name": "G2.5",
        "cust_status": "正常",
        "cust_type": "居民",
        "vent_date": "2020-01-01",
        "bar_code": "BC001",
        "meter_loc": "厨房",
        "comp_name": "测试燃气公司",
        "last_update_time": "2026-05-14T10:30:00",
    }


# === Mock Client Fixtures ===

@pytest.fixture
def mock_api_client():
    """Mock ZrGasApiClient."""
    client = MagicMock(spec=ZrGasApiClient)
    client.get_gas_data = AsyncMock()
    client.send_sms_code = AsyncMock()
    client.verify_sms_code = AsyncMock()
    client.wx_login = AsyncMock()
    client.get_bind_gas_list = AsyncMock()
    client.get_cust_info = AsyncMock()
    client.get_meter_info = AsyncMock()
    client.is_authenticated = False
    return client


# === Config Entry Fixtures ===

@pytest.fixture
def mock_config_entry():
    """Mock ConfigEntry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        "cust_code": "CUST001",
        "token": "test_token",
        "user_id": "test_user_id",
    }
    entry.options = {"scan_interval": 1800}
    entry.title = "测试账户"
    return entry


# === Home Assistant Fixtures ===

@pytest.fixture
def hass():
    """Mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_entries = AsyncMock(return_value=True)
    return hass
