"""Tests for ZrGasApiClient (api.py)."""

import json
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import aiohttp
from aiohttp import ClientError, ClientResponse, ClientSession

from custom_components.zr_gas.api import ZrGasApiClient, ZrGasApiError, ZrGasAuthError
from custom_components.zr_gas.const import (
    BASE_URL,
    HEADERS,
    API_ENDPOINTS,
    ERROR_CODES,
)


# === Helper Functions ===

async def _mock_post_response(
    url: str,
    data: Dict[str, Any],
    headers: Dict[str, str],
    status: int = 200,
    json_data: Dict[str, Any] = None,
) -> MagicMock:
    """Create a mock POST response."""
    mock_resp = MagicMock(spec=ClientResponse)
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data or {"status": "1", "data": {}})
    return mock_resp


# === Test Classes ===

class TestZrGasApiClientInitialization:
    """Test ZrGasApiClient initialization."""

    def test_init_without_auth(self):
        """Test initialization without auth."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session)
        
        assert client._session == session
        assert client._token is None
        assert client._user_id is None

    def test_init_with_auth(self):
        """Test initialization with auth."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session, token="test_token", user_id="test_user")
        
        assert client._token == "test_token"
        assert client._user_id == "test_user"

    def test_is_authenticated_false(self):
        """Test is_authenticated returns False when no token."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session)
        assert client.is_authenticated == False

    def test_is_authenticated_true(self):
        """Test is_authenticated returns True when token exists."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session, token="test_token")
        assert client.is_authenticated == True

    def test_set_auth(self):
        """Test set_auth method."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session)
        
        client.set_auth(token="new_token", user_id="new_user")
        
        assert client._token == "new_token"
        assert client._user_id == "new_user"


class TestGenerateSignature:
    """Test _generate_signature method."""

    def test_generate_signature(self):
        """Test signature generation."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session)
        
        signature = client._generate_signature("CUST001", "1234567890")
        
        # Verify it's a valid MD5 hex digest
        assert len(signature) == 32
        assert all(c in "0123456789abcdef" for c in signature)

    def test_generate_signature_multiple_args(self):
        """Test signature with multiple arguments."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session)
        
        signature = client._generate_signature("CUST001", "1234567890", "extra")
        
        assert len(signature) == 32


class TestGetHeaders:
    """Test _get_headers method."""

    def test_get_headers_no_auth(self):
        """Test headers without auth."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session)
        
        headers = client._get_headers()
        
        assert "accessToken" not in headers
        assert "userId" not in headers
        assert headers["Host"] == HEADERS["Host"]

    def test_get_headers_with_auth(self):
        """Test headers with auth."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session, token="test_token", user_id="test_user")
        
        headers = client._get_headers()
        
        assert headers["accessToken"] == "test_token"
        assert headers["userId"] == "test_user"


class TestPostRequest:
    """Test _post_request method."""

    @pytest.mark.asyncio
    async def test_post_request_success(self):
        """Test successful POST request."""
        session = MagicMock(spec=ClientSession)
        session.post = AsyncMock()
        
        # Mock response
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        mock_resp.json = AsyncMock(return_value={"status": "1", "data": {"key": "value"}})
        
        session.post.return_value = mock_resp
        
        client = ZrGasApiClient(session, token="test_token", user_id="test_user")
        result = await client._post_request("/test", {"data": "value"})
        
        assert result["status"] == "1"
        assert result["data"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_post_request_http_error(self):
        """Test POST request with HTTP error."""
        session = MagicMock(spec=ClientSession)
        session.post = AsyncMock()
        
        mock_resp = AsyncMock()
        mock_resp.status = 404
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        
        session.post.return_value = mock_resp
        
        client = ZrGasApiClient(session, token="test_token")
        
        with pytest.raises(ZrGasApiError, match="HTTP错误"):
            await client._post_request("/test", {"data": "value"})

    @pytest.mark.asyncio
    async def test_post_request_api_error(self):
        """Test POST request with API error (status != 1)."""
        session = MagicMock(spec=ClientSession)
        session.post = AsyncMock()
        
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        mock_resp.json = AsyncMock(return_value={"status": "10001", "message": "系统错误"})
        
        session.post.return_value = mock_resp
        
        client = ZrGasApiClient(session, token="test_token")
        
        with pytest.raises(ZrGasApiError, match="系统错误"):
            await client._post_request("/test", {"data": "value"})

    @pytest.mark.asyncio
    async def test_post_request_auth_error(self):
        """Test POST request with auth error."""
        session = MagicMock(spec=ClientSession)
        session.post = AsyncMock()
        
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        mock_resp.json = AsyncMock(return_value={"status": "20001", "message": "用户未登录"})
        
        session.post.return_value = mock_resp
        
        client = ZrGasApiClient(session, token="test_token")
        
        with pytest.raises(ZrGasAuthError, match="用户未登录"):
            await client._post_request("/test", {"data": "value"})

    @pytest.mark.asyncio
    async def test_post_request_no_auth_raises(self):
        """Test POST request without auth raises ZrGasAuthError."""
        session = MagicMock(spec=ClientSession)
        client = ZrGasApiClient(session)  # No token
        
        with pytest.raises(ZrGasAuthError, match="未认证"):
            await client._post_request("/test", {"data": "value"}, need_auth=True)

    @pytest.mark.asyncio
    async def test_post_request_retry(self):
        """Test POST request retry mechanism."""
        session = MagicMock(spec=ClientSession)
        session.post = AsyncMock()
        
        # First call fails, second succeeds
        mock_resp_fail = AsyncMock()
        mock_resp_fail.status = 500
        mock_resp_fail.__aenter__ = AsyncMock(return_value=mock_resp_fail)
        mock_resp_fail.__aexit__ = AsyncMock(return_value=False)
        
        mock_resp_success = AsyncMock()
        mock_resp_success.status = 200
        mock_resp_success.__aenter__ = AsyncMock(return_value=mock_resp_success)
        mock_resp_success.__aexit__ = AsyncMock(return_value=False)
        mock_resp_success.json = AsyncMock(return_value={"status": "1", "data": {}})
        
        session.post.side_effect = [mock_resp_fail, mock_resp_success]
        
        client = ZrGasApiClient(session, token="test_token")
        
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client._post_request("/test", {"data": "value"}, retries=2)
        
        assert result["status"] == "1"
        assert session.post.call_count == 2


class TestGetGasData:
    """Test get_gas_data method."""

    @pytest.mark.asyncio
    async def test_get_gas_data_success(self, mock_api_client, mock_cust_info, mock_meter_info):
        """Test successful get_gas_data."""
        # Mock the internal methods
        mock_api_client.get_cust_info = AsyncMock(return_value=mock_cust_info)
        mock_api_client.get_meter_info = AsyncMock(return_value=[mock_meter_info])
        
        result = await mock_api_client.get_gas_data("CUST001")
        
        assert "balance" in result
        assert "owe_money" in result
        assert "meter_reading" in result
        assert result["cust_code"] == "CUST001"

    @pytest.mark.asyncio
    async def test_get_gas_data_handles_none_values(self, mock_api_client):
        """Test get_gas_data handles None values."""
        # Return cust_info with None values
        mock_api_client.get_cust_info = AsyncMock(return_value={
            "custName": None,
            "meterNo": None,
            "qtyBalance": None,
            "oweMoney": None,
        })
        mock_api_client.get_meter_info = AsyncMock(return_value=[])
        
        result = await mock_api_client.get_gas_data("CUST001")
        
        assert result["balance"] == 0
        assert result["owe_money"] == 0


class TestSendSmsCode:
    """Test send_sms_code method."""

    @pytest.mark.asyncio
    async def test_send_sms_code_success(self, mock_api_client):
        """Test successful SMS code sending."""
        mock_api_client._post_request = AsyncMock(return_value={"status": "1", "message": "成功"})
        
        result = await mock_api_client.send_sms_code("13800138000")
        
        assert result is True


class TestVerifySmsCode:
    """Test verify_sms_code method."""

    @pytest.mark.asyncio
    async def test_verify_sms_code_success(self, mock_api_client):
        """Test successful SMS code verification."""
        mock_api_client._post_request = AsyncMock(return_value={
            "status": "1",
            "data": {
                "accessToken": "test_token",
                "userId": "test_user",
                "expireTime": "2026-06-01",
            }
        })
        
        result = await mock_api_client.verify_sms_code("13800138000", "123456")
        
        assert result["token"] == "test_token"
        assert result["user_id"] == "test_user"
        assert mock_api_client._token == "test_token"
        assert mock_api_client._user_id == "test_user"
