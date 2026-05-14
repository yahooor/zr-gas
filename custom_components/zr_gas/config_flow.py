"""中燃在线集成 - 配置流

实现步骤:
1. 选择认证方式（短信验证码 / Token 直接导入）
2A. 短信登录表单（手机号 + 验证码）
2B. Token 导入表单
3. 账户列表和绑定确认
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import ZrGasApiClient, ZrGasApiError, ZrGasAuthError
from .const import DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)

# 配置步骤
STEP_AUTH_METHOD = "auth_method"
STEP_SMS_LOGIN = "sms_login"
STEP_TOKEN_IMPORT = "token_import"
STEP_ACCOUNT_LIST = "account_list"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """配置流处理器"""

    VERSION = 1

    def __init__(self):
        self._api_client: Optional[ZrGasApiClient] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_data: Dict[str, Any] = {}
        self._accounts: List[Dict[str, Any]] = []
        self._phone: str = ""

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """步骤0: 选择认证方式"""
        errors: Dict[str, str] = {}

        if user_input is not None:
            auth_method = user_input.get("auth_method", STEP_SMS_LOGIN)
            if auth_method == STEP_SMS_LOGIN:
                return await self.async_step_sms_login()
            else:
                return await self.async_step_token_import()

        return self.async_show_form(
            step_id=STEP_AUTH_METHOD,
            data_schema=vol.Schema({
                vol.Required("auth_method", default=STEP_SMS_LOGIN): vol.In({
                    STEP_SMS_LOGIN: "短信验证码登录（推荐）",
                    STEP_TOKEN_IMPORT: "Token 直接导入（抓包获取）",
                }),
            }),
            errors=errors,
            description_placeholders={"name": NAME},
        )

    async def async_step_sms_login(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """步骤1: 短信验证码登录"""
        errors: Dict[str, str] = {}

        if user_input is not None:
            phone = user_input.get(CONF_USERNAME, "")
            sms_code = user_input.get("sms_code", "")

            if not phone:
                errors["base"] = "phone_required"
            elif not sms_code:
                # 仅提供手机号，发送验证码
                try:
                    async with aiohttp.ClientSession() as session:
                        self._api_client = ZrGasApiClient(session)
                        await self._api_client.send_sms_code(phone)
                        self._phone = phone
                    return self.async_show_form(
                        step_id=STEP_SMS_LOGIN,
                        data_schema=vol.Schema({
                            vol.Required(CONF_USERNAME, default=phone): str,
                            vol.Required("sms_code"): str,
                        }),
                        errors=errors,
                        description_placeholders={
                            "status": f"验证码已发送至 {phone[:3]}****{phone[-4:]}",
                        },
                    )
                except ZrGasApiError as e:
                    errors["base"] = "sms_error"
                    _LOGGER.error(f"发送验证码失败: {e}")

            else:
                # 验证验证码
                try:
                    async with aiohttp.ClientSession() as session:
                        self._api_client = ZrGasApiClient(session)
                        auth_result = await self._api_client.verify_sms_code(phone, sms_code)
                        self._auth_data = {
                            "token": auth_result.get("token"),
                            "user_id": auth_result.get("user_id"),
                        }

                    # 获取账户列表
                    accounts = await self._api_client.get_bind_gas_list()
                    self._accounts = accounts

                    if not self._accounts:
                        return self.async_show_form(
                            step_id=STEP_SMS_LOGIN,
                            data_schema=vol.Schema({
                                vol.Required(CONF_USERNAME): str,
                                vol.Required("sms_code"): str,
                            }),
                            errors={"base": "no_accounts"},
                            description_placeholders={"status": "未找到绑定的燃气账户"},
                        )

                    return await self.async_step_account_list()

                except ZrGasAuthError as e:
                    errors["base"] = "auth_error"
                    _LOGGER.error(f"认证失败: {e}")
                except ZrGasApiError as e:
                    errors["base"] = "api_error"
                    _LOGGER.error(f"API错误: {e}")

        return self.async_show_form(
            step_id=STEP_SMS_LOGIN,
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Optional("sms_code"): str,
            }),
            errors=errors,
            description_placeholders={
                "status": "请输入手机号，点击获取验证码后再填写",
            },
        )

    async def async_step_token_import(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """步骤1B: Token 直接导入"""
        errors: Dict[str, str] = {}

        if user_input is not None:
            token = user_input.get(CONF_TOKEN, "")
            user_id = user_input.get("user_id", "")

            if not token:
                errors["base"] = "token_required"
            else:
                try:
                    async with aiohttp.ClientSession() as session:
                        self._api_client = ZrGasApiClient(session, token=token, user_id=user_id)
                        self._auth_data = {
                            "token": token,
                            "user_id": user_id,
                        }

                        # 验证 Token 是否有效
                        accounts = await self._api_client.get_bind_gas_list()
                        self._accounts = accounts

                    if not self._accounts:
                        return self.async_show_form(
                            step_id=STEP_TOKEN_IMPORT,
                            data_schema=vol.Schema({
                                vol.Required(CONF_TOKEN): str,
                                vol.Optional("user_id"): str,
                            }),
                            errors={"base": "no_accounts"},
                            description_placeholders={"status": "Token无效或无绑定账户"},
                        )

                    return await self.async_step_account_list()

                except ZrGasAuthError as e:
                    errors["base"] = "invalid_token"
                    _LOGGER.error(f"Token无效: {e}")
                except ZrGasApiError as e:
                    errors["base"] = "api_error"
                    _LOGGER.error(f"API错误: {e}")

        return self.async_show_form(
            step_id=STEP_TOKEN_IMPORT,
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN): str,
                vol.Optional("user_id"): str,
            }),
            errors=errors,
            description_placeholders={
                "help": "从抓包数据中获取 accessToken 和 userId",
            },
        )

    async def async_step_account_list(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """步骤2: 账户列表选择"""
        errors: Dict[str, str] = {}

        if user_input is not None:
            selected_codes = user_input.get("accounts", [])

            if not selected_codes:
                errors["base"] = "select_required"
            else:
                # 获取第一个选中账户的完整信息
                selected_code = selected_codes[0]
                account_data = next(
                    (acc for acc in self._accounts if acc.get("custCode") == selected_code),
                    self._accounts[0] if self._accounts else {},
                )

                return await self._create_entry(account_data)

        # 生成账户选项
        account_options = {
            acc.get("custCode", idx): f"{acc.get('meterNo', '未知表号')} - {acc.get('address', '未知地址')[:20]}..."
            for idx, acc in enumerate(self._accounts)
        }

        return self.async_show_form(
            step_id=STEP_ACCOUNT_LIST,
            data_schema=vol.Schema({
                vol.Required("accounts"): [vol.In(list(account_options.keys()))],
            }),
            errors=errors,
            description_placeholders={
                "count": str(len(self._accounts)),
            },
        )

    async def _create_entry(self, account: Dict[str, Any]) -> FlowResult:
        """创建配置条目"""
        cust_code = account.get("custCode", "default")
        title = f"{NAME} - {account.get('meterNo', cust_code)}"

        data = {
            **self._auth_data,
            "cust_code": cust_code,
            "account": account,
        }

        await self.async_set_unique_id(f"{DOMAIN}_{cust_code}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=title, data=data)


@callback
def _async_get_options_flow(config_entry):
    """获取选项流"""
    return ZrGasOptionsFlowHandler(config_entry)


class ZrGasOptionsFlowHandler(config_entries.OptionsFlow):
    """选项处理器"""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """初始化选项"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "scan_interval",
                    default=self._config_entry.options.get("scan_interval", 1800),
                ): vol.All(vol.Coerce(int), vol.Range(min=300, max=86400)),
            }),
        )
