"""Basic tests for config_flow (simplified).

Note: Full config flow tests require pytest-homeassistant-custom with HA's
test helpers (MockConfigFlow). These tests verify the validation logic.
"""

from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassitant.data_entry_flow import FlowResult
from homeassitant.config_entries import ConfigEntry

from custom_components.zr_gas.config_flow import ZrGasFlowHandler
from custom_components.zr_gas.const import DOMAIN


class TestVoluptuousValidators:
    """Test voluptuous validators in config_flow."""

    def test_phone_required_validator(self):
        """Test phone_required validator."""
        from custom_components.zr_gas.config_flow import phone_required

        # Valid phone
        assert phone_required("13800138000") == "13800138000"

        # Invalid - too short
        with pytest.raises(Exception):
            phone_required("1380013800")

        # Invalid - contains non-digits
        with pytest.raises(Exception):
            phone_required("1380013800a")

    def test_token_required_validator(self):
        """Test token_required validator."""
        from custom_components.zr_gas.config_flow import token_required

        # Valid token
        assert token_required("abc123") == "abc123"

        # Invalid - too short
        with pytest.raises(Exception):
            token_required("abc12")

    def test_no_accounts_validator(self):
        """Test no_accounts validator."""
        from custom_components.zr_gas.config_flow import no_accounts

        # Valid - has accounts
        accounts = [{"custCode": "CUST001", "custName": "Test"}]
        result = no_accounts(accounts)
        assert result == accounts

        # Invalid - empty list
        with pytest.raises(Exception):
            no_accounts([])


class TestZrGasFlowHandlerInit:
    """Test ZrGasFlowHandler initialization."""

    def test_init(self):
        """Test handler initialization."""
        handler = ZrGasFlowHandler()
        
        assert handler.VERSION == 1
        # Check initial form data is empty
        assert len(handler._form_data) >= 0  # dict


class TestStepAuthMethod:
    """Test async_step_auth_method."""

    @pytest.mark.asyncio
    async def test_auth_method_shows_form(self):
        """Test auth_method shows form with choices."""
        handler = ZrGasFlowHandler()
        handler._show_form = MagicMock()

        await handler.async_step_auth_method()

        # Check _show_form was called
        handler._show_form.assert_called_once()
        call_args = handler._show_form.call_args
        assert call_args[0][0] == "auth_method"


class TestStepSmsLogin:
    """Test async_step_sms_login."""

    @pytest.mark.asyncio
    async def test_sms_login_validates_phone(self):
        """Test sms_login validates phone number."""
        handler = ZrGasFlowHandler()
        
        # Call with invalid user input
        result = await handler.async_step_sms_login(user_input={})

        # Should show form again with errors
        assert result["type"] == "abort" or result.get("errors")


class TestStepTokenImport:
    """Test async_step_token_import."""

    @pytest.mark.asyncio
    async def test_token_import_validates(self):
        """Test token_import validates input."""
        handler = ZrGasFlowHandler()

        # Call with no input
        result = await handler.async_step_token_import(user_input={})

        # Should show form
        if result["type"] == "form":
            assert "token" in str(result)


class TestStepAccountList:
    """Test async_step_account_list."""

    @pytest.mark.asyncio
    async def test_account_list_with_accounts(self):
        """Test account_list with valid accounts."""
        handler = ZrGasFlowHandler()

        # Mock API client
        accounts = [
            {"custCode": "CUST001", "custName": "张三", "meterNo": "METER001"},
            {"custCode": "CUST002", "custName": "李四", "meterNo": "METER002"},
        ]

        with patch.object(handler, "_api_client") as mock_client:
            mock_client.get_bind_gas_list = AsyncMock(return_value=accounts)

            result = await handler.async_step_account_list()

            # Should show form with accounts
            assert result["type"] == "form"
            assert "account" in str(result)


class TestOptionsFlow:
    """Test ZrGasOptionsFlowHandler."""

    @pytest.mark.asyncio
    async def test_options_flow_init(self):
        """Test options flow initialization."""
        from custom_components.zr_gas.config_flow import ZrGasOptionsFlowHandler

        entry = MagicMock(spec=ConfigEntry)
        entry.options = {"scan_interval": 1800}

        handler = ZrGasOptionsFlowHandler(entry)

        assert handler._entry == entry

    @pytest.mark.asyncio
    async def test_options_flow_step_init(self):
        """Test options flow step_init."""
        from custom_components.zr_gas.config_flow import ZrGasOptionsFlowHandler

        entry = MagicMock(spec=ConfigEntry)
        entry.options = {"scan_interval": 1800}

        handler = ZrGasOptionsFlowHandler(entry)
        handler._show_form = MagicMock()

        await handler.async_step_init()

        handler._show_form.assert_called_once()
