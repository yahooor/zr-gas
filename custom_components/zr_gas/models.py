"""Data models for the 中燃在线 (ZR Gas) integration.

Defines dataclasses for customer information, billing records,
tiered pricing configuration, and statistics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ZrGasCustomer:
    """绑定的燃气客户摘要信息。

    从 getBindGasCustList 接口返回。
    """

    cust_code: str
    cust_name: str


@dataclass
class ZrGasCustomerDetail:
    """客户详细信息。

    从 findCustInfoByCustCodeAndCustName 接口返回。
    """

    cust_code: str
    cust_name: str
    cust_address: str
    balance: float
    owe_money: float = 0.0
    last_record: float = 0.0
    qty_meter_balance: float = 0.0
    purch_times: int = 0
    last_record_time: str = ""
    meter_no: str = ""
    meter_form_name: str = ""
    card_no: str = ""
    comp_name: str = ""
    cust_status: str = ""
    fee: str = ""


@dataclass
class ZrGasBill:
    """单条缴费/账单记录。

    从 getCustomerMoneyList 接口返回。
    """

    period: str  # 账期，格式 YYYYMM
    usage_volume: float  # 用气量 (m³)
    usage_amount: float  # 费用金额 (CNY)
    unit_price: float  # 单价 (CNY/m³)


@dataclass
class TierConfig:
    """阶梯气价配置。

    三档年度阶梯计价：
    - 第一档: 0 ~ tier_2_start m³，价格 tier_1_price
    - 第二档: tier_2_start ~ tier_3_start m³，价格 tier_2_price
    - 第三档: tier_3_start 以上，价格 tier_3_price
    - 阶梯周期起始日: tier_cycle_start_md (MM-DD 格式)
    """

    tier_2_start: float = 400.0
    tier_3_start: float = 1680.0
    tier_1_price: float = 2.99
    tier_2_price: float = 3.44
    tier_3_price: float = 4.34
    tier_cycle_start_md: str = "01-01"

    def get_tier_info(
        self, annual_usage: float
    ) -> tuple[int, float, float]:
        """根据年度累计用量返回当前阶梯信息。

        Args:
            annual_usage: 年度累计用气量 (m³)

        Returns:
            (tier_number, current_price, remaining_in_tier)
            tier_number: 1/2/3
            current_price: 当前阶梯单价
            remaining_in_tier: 当前阶梯剩余量 (inf 表示无上限)
        """
        if annual_usage <= self.tier_2_start:
            return 1, self.tier_1_price, self.tier_2_start - annual_usage
        elif annual_usage <= self.tier_3_start:
            return 2, self.tier_2_price, self.tier_3_start - annual_usage
        else:
            return 3, self.tier_3_price, float("inf")

    def calculate_cost(self, usage: float) -> float:
        """根据用气量计算费用。

        Args:
            usage: 用气量 (m³)

        Returns:
            费用金额 (CNY)
        """
        if usage <= self.tier_2_start:
            return usage * self.tier_1_price
        elif usage <= self.tier_3_start:
            return self.tier_2_start * self.tier_1_price + (
                usage - self.tier_2_start
            ) * self.tier_2_price
        else:
            return (
                self.tier_2_start * self.tier_1_price
                + (self.tier_3_start - self.tier_2_start) * self.tier_2_price
                + (usage - self.tier_3_start) * self.tier_3_price
            )


@dataclass
class MonthlyStat:
    """月度统计数据。"""

    year: int
    month: int
    usage: float = 0.0
    cost: float = 0.0
    unit_price: float = 0.0
    days: int = 0
    avg_daily_usage: float = 0.0

    @property
    def period(self) -> str:
        """返回账期字符串 (YYYYMM)。"""
        return f"{self.year}{self.month:02d}"


@dataclass
class YearlyStat:
    """年度统计数据。"""

    year: int
    usage: float = 0.0
    cost: float = 0.0
    avg_monthly_usage: float = 0.0
    peak_month: Optional[int] = None
    peak_month_usage: float = 0.0
    monthly_stats: list[MonthlyStat] = field(default_factory=list)

    @property
    def tier(self) -> int:
        """返回当前阶梯 (根据年度用量估算)。"""
        if self.usage <= 400:
            return 1
        elif self.usage <= 1680:
            return 2
        return 3


@dataclass
class ZrGasDeviceData:
    """聚合的设备数据。

    用于传感器状态更新的综合数据对象。
    """

    cust_code: str
    cust_name: str
    balance: float
    owe_money: float = 0.0
    monthly_usage: float = 0.0
    monthly_cost: float = 0.0
    annual_usage: float = 0.0
    annual_cost: float = 0.0
    unit_price: float = 2.99
    meter_no: str = ""
    meter_form_name: str = ""
    card_no: str = ""
    qty_meter_balance: float = 0.0
    last_record: float = 0.0
    last_record_time: str = ""
    purch_times: int = 0
    cust_address: str = ""
    comp_name: str = ""
    current_tier: int = 1
    current_tier_price: float = 2.99
    tier_cycle_start: str = ""
    period: str = ""
    tier_config: Optional[TierConfig] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式。"""
        return {
            "cust_code": self.cust_code,
            "cust_name": self.cust_name,
            "balance": self.balance,
            "owe_money": self.owe_money,
            "monthly_usage": self.monthly_usage,
            "monthly_cost": self.monthly_cost,
            "annual_usage": self.annual_usage,
            "annual_cost": self.annual_cost,
            "unit_price": self.unit_price,
            "meter_no": self.meter_no,
            "meter_form_name": self.meter_form_name,
            "card_no": self.card_no,
            "qty_meter_balance": self.qty_meter_balance,
            "last_record": self.last_record,
            "last_record_time": self.last_record_time,
            "purch_times": self.purch_times,
            "cust_address": self.cust_address,
            "comp_name": self.comp_name,
            "current_tier": self.current_tier,
            "current_tier_price": self.current_tier_price,
            "tier_cycle_start": self.tier_cycle_start,
            "period": self.period,
        }