"""中燃在线 API 通信模块

基于抓包数据分析:
- 域名: zrds.95007.com
- 认证方式: accessToken + userId 请求头
- 签名算法: MD5(custCode + timeStamp + salt)
- 平台: mp-weixin
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from .const import (
    BASE_URL,
    HEADERS,
    API_ENDPOINTS,
    WECHAT_APP_ID,
    SENSOR_TYPES,
    ERROR_CODES,
)

_LOGGER = logging.getLogger(__name__)


class ZrGasApiError(Exception):
    """API 错误基类"""
    pass


class ZrGasAuthError(ZrGasApiError):
    """认证错误"""
    pass


class ZrGasApiClient:
    """中燃在线 API 客户端"""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self._session = session
        self._token = token
        self._user_id = user_id

    @staticmethod
    def _generate_signature(*args) -> str:
        """生成签名

        基于抓包分析: MD5(custCode + timeStamp + salt)
        """
        sign_str = "".join(str(arg) for arg in args)
        sign_str += "ZR_GAS_SALT"  # Salt 值（待确认）
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = dict(HEADERS)
        if self._token:
            headers["accessToken"] = self._token
        if self._user_id:
            headers["userId"] = str(self._user_id)
        return headers

    async def _post_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        need_auth: bool = True,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """发送 POST 请求，带重试机制

        Args:
            endpoint: API 端点
            data: 请求数据
            need_auth: 是否需要认证
            retries: 重试次数（默认3次）
        """
        url = BASE_URL + endpoint
        headers = self._get_headers()

        if need_auth and not self._token:
            raise ZrGasAuthError("未认证，请先登录")

        last_error = None
        for attempt in range(retries):
            try:
                async with self._session.post(
                    url,
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        raise ZrGasApiError(f"HTTP错误: {resp.status}")

                    result = await resp.json()
                    status = result.get("status")
                    message = result.get("message", "")

                    if status != "1":
                        error_msg = ERROR_CODES.get(str(status), message)
                        _LOGGER.error(f"API错误 [{status}]: {error_msg}")

                        if status in ["20001", "20002", "20003"]:
                            raise ZrGasAuthError(error_msg)
                        raise ZrGasApiError(f"{error_msg} (code: {status})")

                    return result

            except (aiohttp.ClientError, ZrGasApiError) as e:
                last_error = e
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                    _LOGGER.warning(f"请求失败，{wait_time}s后重试 ({attempt + 1}/{retries}): {e}")
                    await asyncio.sleep(wait_time)
                    continue
                _LOGGER.error(f"请求最终失败: {e}")

        raise last_error

    async def send_sms_code(self, phone: str) -> bool:
        """发送短信验证码

        基于抓包: POST /crm_controller/user/sendSmsCode
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = self._generate_signature(phone, timestamp)

        data = {
            "mobile": phone,
            "timeStamp": timestamp,
            "signature": signature,
            "platform": "mp-weixin",
            "appId": WECHAT_APP_ID,
        }

        result = await self._post_request(
            API_ENDPOINTS["send_sms"],
            data,
            need_auth=False,
        )

        _LOGGER.info(f"验证码已发送到 {phone[:3]}****{phone[-4:]}")
        return result.get("status") == "1"

    async def verify_sms_code(self, phone: str, code: str) -> Dict[str, Any]:
        """验证短信验证码并登录

        基于抓包: POST /crm_controller/user/verifySmsCode
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = self._generate_signature(phone, code, timestamp)

        data = {
            "mobile": phone,
            "smsCode": code,
            "timeStamp": timestamp,
            "signature": signature,
            "platform": "mp-weixin",
            "appId": WECHAT_APP_ID,
        }

        result = await self._post_request(
            API_ENDPOINTS["verify_sms"],
            data,
            need_auth=False,
        )

        # 提取认证信息
        data_result = result.get("data", {})
        self._token = data_result.get("accessToken", data_result.get("token"))
        self._user_id = data_result.get("userId", data_result.get("user_id"))

        return {
            "token": self._token,
            "user_id": self._user_id,
            "expire_time": data_result.get("expireTime"),
        }

    async def wx_login(self, code: str) -> Dict[str, Any]:
        """微信登录

        基于抓包: POST /crm_controller/user/wxLogin
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = self._generate_signature(code, timestamp)

        data = {
            "jsCode": code,
            "timeStamp": timestamp,
            "signature": signature,
            "platform": "mp-weixin",
            "appId": WECHAT_APP_ID,
        }

        result = await self._post_request(
            API_ENDPOINTS["wx_login"],
            data,
            need_auth=False,
        )

        data_result = result.get("data", {})
        self._token = data_result.get("accessToken", data_result.get("token"))
        self._user_id = data_result.get("userId", data_result.get("user_id"))

        return {
            "token": self._token,
            "user_id": self._user_id,
        }

    async def get_bind_gas_list(self) -> List[Dict[str, Any]]:
        """获取绑定的燃气账户列表

        基于抓包: POST /crm_controller/user/getBindGasCustList

        响应字段:
        - custCode: 客户编号
        - meterNo: 燃气表号
        - address: 地址
        - qtyMeterBalance: 气量余额
        - oweMoney: 欠费金额
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))

        data = {
            "userId": self._user_id,
            "timeStamp": timestamp,
        }
        data["signature"] = self._generate_signature(
            self._user_id, timestamp
        )

        result = await self._post_request(
            API_ENDPOINTS["bind_list"],
            data,
        )

        accounts = result.get("data", [])
        _LOGGER.info(f"获取到 {len(accounts)} 个绑定账户")

        return accounts

    async def get_cust_info(self, cust_code: str, cust_name: str = "") -> Dict[str, Any]:
        """获取客户详细信息

        基于抓包: POST /crm_controller/user/findCustInfoByCustCodeAndCustName

        响应字段（关键）:
        - custCode: 客户编号
        - custName: 客户姓名（部分隐藏）
        - meterNo: 燃气表号
        - address: 地址
        - qtyMeterBalance: 气量余额
        - qtyBalance: 余额
        - oweMoney: 欠费金额
        - lastRecord: 上次表读数
        - lastRecordTime: 上次抄表时间
        - countMoney: 当月费用
        - purchTimes: 购气次数
        - newOweMoney: 新欠费金额
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = self._generate_signature(cust_code, cust_name, timestamp)

        data = {
            "custCode": cust_code,
            "custName": cust_name,
            "timeStamp": timestamp,
            "signature": signature,
        }

        result = await self._post_request(
            API_ENDPOINTS["cust_info"],
            data,
        )

        return result.get("data", {})

    async def get_meter_info(self, cust_code: str, envir: str = "2") -> List[Dict[str, Any]]:
        """获取燃气表信息

        基于抓包: POST /crm_controller/user/getMeterInfo

        响应字段:
        - meterId: 表ID
        - meterNo: 表号
        - meterType: 表类型
        - qtyMeterBalance: 气量余额
        - purchTimes: 购气次数
        - cardType: 卡类型
        - cardNo: 卡号
        """
        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = self._generate_signature(cust_code, envir, timestamp)

        data = {
            "custCode": cust_code,
            "envir": envir,
            "timeStamp": timestamp,
            "signature": signature,
        }

        result = await self._post_request(
            API_ENDPOINTS["meter_info"],
            data,
        )

        return result.get("data", [])

    async def get_gas_data(self, cust_code: str) -> Dict[str, Any]:
        """获取燃气数据（综合）

        使用并行请求优化性能，同步获取客户信息和表信息
        """
        # 并行获取客户信息和表信息
        cust_info, meter_info = await asyncio.gather(
            self.get_cust_info(cust_code),
            self.get_meter_info(cust_code),
        )
        meter_data = meter_info[0] if meter_info else {}

        # 合并数据
        return {
            # 基本信息
            "cust_code": cust_code,
            "cust_name": cust_info.get("custName", ""),
            "meter_no": cust_info.get("meterNo", ""),
            "address": cust_info.get("address", ""),
            "mobile": cust_info.get("mobile", ""),

            # 余额/费用类
            "balance": float(cust_info.get("qtyBalance", 0) or 0),
            "owe_money": float(cust_info.get("oweMoney", 0) or 0),
            "new_owe_money": float(cust_info.get("newOweMoney", 0) or 0),
            "award_money": float(cust_info.get("awardMoney", 0) or 0),
            "monthly_cost": float(cust_info.get("countMoney", 0) or 0),
            "fee": float(cust_info.get("fee", 0) or 0),

            # 用量/气量类
            "meter_reading": float(cust_info.get("lastRecord", 0) or 0),
            "gas_balance": float(cust_info.get("qtyMeterBalance", 0) or 0),
            "max_gas": float(cust_info.get("maxGas", 0) or 0),
            "monthly_usage": 0.0,  # 需要从账单接口获取

            # 价格类
            "gas_price": float(cust_info.get("price", 0) or 0),

            # 次数/计数类
            "purch_times": int(cust_info.get("purchTimes", 0) or 0),

            # 时间类
            "last_record_time": cust_info.get("lastRecordTime", ""),

            # 信息类
            "card_type": cust_info.get("cardType", meter_data.get("cardType", "")),
            "card_no": cust_info.get("cardNo", meter_data.get("cardNo", "")),
            "meter_type": cust_info.get("metertype", ""),
            "meter_form_name": cust_info.get("meterFormName", meter_data.get("meterFormName", "")),
            "cust_status": cust_info.get("custStatus", ""),
            "cust_type": cust_info.get("custType", ""),
            "vent_date": meter_data.get("ventDate", ""),
            "bar_code": meter_data.get("barCode", ""),
            "meter_loc": meter_data.get("meterloc", ""),

            # 公司信息
            "comp_name": cust_info.get("compName", ""),
        }

    async def get_monthly_usage(self, cust_code: str, year: int = None, month: int = None) -> Dict[str, Any]:
        """获取月度用量

        基于抓包: POST /crm_controller/gas/queryMonthlyUsage
        """
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month

        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = self._generate_signature(cust_code, year, month, timestamp)

        data = {
            "custCode": cust_code,
            "year": str(year),
            "month": str(month),
            "timeStamp": timestamp,
            "signature": signature,
        }

        result = await self._post_request(
            API_ENDPOINTS["monthly_usage"],
            data,
        )

        return result.get("data", {})

    async def get_bill_history(self, cust_code: str, year: int = None) -> List[Dict[str, Any]]:
        """获取账单历史

        基于抓包: POST /crm_controller/gas/queryBillHistory
        """
        if year is None:
            year = datetime.now().year

        timestamp = str(int(datetime.now().timestamp() * 1000))
        signature = self._generate_signature(cust_code, year, timestamp)

        data = {
            "custCode": cust_code,
            "year": str(year),
            "timeStamp": timestamp,
            "signature": signature,
        }

        result = await self._post_request(
            API_ENDPOINTS["bill_history"],
            data,
        )

        return result.get("data", [])

    @property
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return bool(self._token)

    @property
    def user_id(self) -> Optional[str]:
        """获取用户 ID"""
        return self._user_id

    @property
    def token(self) -> Optional[str]:
        """获取访问令牌"""
        return self._token

    def set_auth(self, token: str, user_id: str):
        """设置认证信息（用于 Token 直接导入）"""
        self._token = token
        self._user_id = user_id
        _LOGGER.info(f"已设置认证: userId={user_id}")
