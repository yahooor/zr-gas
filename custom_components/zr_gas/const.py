"""中燃在线集成 - 常量定义

API 基于中燃在线平台抓包数据分析:
- 域名: zrds.95007.com
- 平台: mp-weixin
- 签名: MD5(参数拼接 + salt)
"""

DOMAIN = "zr_gas"
NAME = "中燃在线"
VERSION = "1.0.7"

# 配置条目常量
CONF_USER_ID = "user_id"
CONF_CUST_CODE = "cust_code"

# API 配置（基于抓包确认）
BASE_URL = "https://zrds.95007.com"

# API 端点（基于抓包确认）
API_ENDPOINTS = {
    # 登录认证
    "send_sms": "/crm_controller/user/sendSmsCode",  # 发送短信验证码
    "verify_sms": "/crm_controller/user/verifySmsCode",  # 验证短信码
    "wx_login": "/crm_controller/user/wxLogin",  # 微信登录

    # 用户信息
    "bind_list": "/crm_controller/user/getBindGasCustList",  # 获取绑定账户列表
    "cust_info": "/crm_controller/user/findCustInfoByCustCodeAndCustName",  # 客户详细信息
    "meter_info": "/crm_controller/user/getMeterInfo",  # 燃气表信息

    # 数据查询
    "gas_data": "/crm_controller/gas/queryGasInfo",  # 燃气数据查询
    "monthly_usage": "/crm_controller/gas/queryMonthlyUsage",  # 月度用量
    "bill_history": "/crm_controller/gas/queryBillHistory",  # 账单历史

    # 新发现接口
    "gas_consumption": "/crm_controller/user/getGasConsumption",  # 用气量记录
    "payment_list": "/crm_controller/payfee/getPaymentList",  # 缴费记录
}

# 请求头配置（基于抓包确认）
HEADERS = {
    "Host": "zrds.95007.com",
    "Content-Type": "application/x-www-form-urlencoded",
    "accessFrom": "yphpaymp",
    "platform": "mp-weixin",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.73(0x18004927) NetType/WIFI Language/zh_CN",
    "Referer": "https://servicewechat.com/wx2082cbdc25b3b8e6/107/page-frame.html",
}

# 微信小程序 AppID（基于抓包确认）
WECHAT_APP_ID = "wx2082cbdc25b3b8e6"

# 传感器类型定义（基于 HAR 抓包数据分析）
SENSOR_TYPES = {
    # === 余额/费用类 ===
    "balance": {
        "name": "账户余额",
        "unit": "CNY",
        "icon": "mdi:currency-cny",
        "device_class": "monetary",
        "api_field": "qtyBalance",
        "description": "账户余额（负数表示欠费）",
    },
    "owed_amount": {
        "name": "欠费金额",
        "unit": "CNY",
        "icon": "mdi:alert-circle",
        "device_class": "monetary",
        "api_field": "oweMoney",
        "description": "账户欠费金额",
    },
    "new_owe_money": {
        "name": "最新欠费",
        "unit": "CNY",
        "icon": "mdi:alert-circle-outline",
        "device_class": "monetary",
        "api_field": "newOweMoney",
        "description": "最新欠费金额",
    },
    "award_money": {
        "name": "奖励金额",
        "unit": "CNY",
        "icon": "mdi:gift",
        "device_class": "monetary",
        "api_field": "awardMoney",
        "description": "奖励/返利金额",
    },
    "monthly_cost": {
        "name": "月度费用",
        "unit": "CNY",
        "icon": "mdi:calculator",
        "device_class": "monetary",
        "api_field": "countMoney",
        "description": "当月累计费用",
    },
    "fee": {
        "name": "当前账单",
        "unit": "CNY",
        "icon": "mdi:receipt",
        "device_class": "monetary",
        "api_field": "fee",
        "description": "当前账单金额",
    },

    # === 用量/气量类 ===
    "monthly_usage": {
        "name": "月度用量",
        "unit": "m³",
        "icon": "mdi:fire",
        "device_class": "gas",
        "api_field": "monthlyUsage",
        "description": "当月累计用气量",
    },
    "meter_reading": {
        "name": "表读数",
        "unit": "m³",
        "icon": "mdi:gauge",
        "device_class": "gas",
        "api_field": "lastRecord",
        "description": "累计表读数",
    },
    "gas_balance": {
        "name": "气量余额",
        "unit": "m³",
        "icon": "mdi:gas-cylinder",
        "device_class": "gas",
        "api_field": "qtyMeterBalance",
        "description": "气量余额（智能表）",
    },
    "max_gas": {
        "name": "最大购气量",
        "unit": "m³",
        "icon": "mdi:arrow-up-bold",
        "device_class": "gas",
        "api_field": "maxGas",
        "description": "最大允许购气量",
    },

    # === 价格类 ===
    "gas_price": {
        "name": "燃气单价",
        "unit": "CNY",
        "icon": "mdi:currency-usd",
        "device_class": "monetary",
        "api_field": "price",
        "description": "当前燃气单价",
    },

    # === 次数/计数类 ===
    "purch_times": {
        "name": "购气次数",
        "unit": None,
        "icon": "mdi:counter",
        "device_class": None,
        "api_field": "purchTimes",
        "description": "累计购气次数",
    },

    # === 时间类 ===
    "last_record_time": {
        "name": "最后抄表日期",
        "unit": None,
        "icon": "mdi:calendar-clock",
        "device_class": "timestamp",
        "api_field": "lastRecordTime",
        "description": "上次抄表时间",
    },

    # === 信息类 ===
    "card_type": {
        "name": "卡类型",
        "unit": None,
        "icon": "mdi:card-account-details",
        "device_class": None,
        "api_field": "cardType",
        "description": "燃气卡类型",
    },
    "card_no": {
        "name": "卡号",
        "unit": None,
        "icon": "mdi:numeric",
        "device_class": None,
        "api_field": "cardNo",
        "description": "燃气卡号",
    },
    "meter_type": {
        "name": "燃气表类型",
        "unit": None,
        "icon": "mdi:meter-electric",
        "device_class": None,
        "api_field": "metertype",
        "description": "燃气表类型",
    },
    "meter_form_name": {
        "name": "燃气表型号",
        "unit": None,
        "icon": "mdi:meter-gas",
        "device_class": None,
        "api_field": "meterFormName",
        "description": "燃气表型号名称",
    },
    "cust_status": {
        "name": "客户状态",
        "unit": None,
        "icon": "mdi:account-check",
        "device_class": None,
        "api_field": "custStatus",
        "description": "客户账户状态",
    },
    "cust_type": {
        "name": "客户类型",
        "unit": None,
        "icon": "mdi:account-group",
        "device_class": None,
        "api_field": "custType",
        "description": "客户类型",
    },
    "vent_date": {
        "name": "通气日期",
        "unit": None,
        "icon": "mdi:calendar-start",
        "device_class": "timestamp",
        "api_field": "ventDate",
        "description": "通气日期",
    },
    "bar_code": {
        "name": "表具条码",
        "unit": None,
        "icon": "mdi:barcode",
        "device_class": None,
        "api_field": "barCode",
        "description": "燃气表条形码",
    },
    "meter_loc": {
        "name": "表具位置",
        "unit": None,
        "icon": "mdi:map-marker",
        "device_class": None,
        "api_field": "meterloc",
        "description": "燃气表安装位置",
    },

    # === 与旧版 zr-gas-ha 兼容的传感器别名 ===
    "purchase_count": {
        "name": "购气次数",
        "unit": "次",
        "icon": "mdi:counter",
        "device_class": None,
        "api_field": "purchTimes",
        "description": "累计购气次数（兼容旧版）",
    },
}

# 默认配置（与旧版 zr-gas-ha 兼容）
DEFAULT_SCAN_INTERVAL = 21600  # 6小时（与旧版兼容）
MIN_SCAN_INTERVAL = 300  # 最小刷新间隔（5分钟）

# === 与旧版 zr-gas-ha 兼容的传感器别名 ===
# 旧版名称 -> 新版名称 映射
SENSOR_ALIASES = {
    # 余额/费用类
    "owe_money": "owed_amount",  # 兼容旧版 owe_money
    "monthly_usage": "monthly_usage",  # 兼容
    "monthly_cost": "monthly_cost",  # 兼容
    "gas_balance": "gas_balance",  # 兼容
    "purchase_count": "purch_times",  # 兼容旧版 purchase_count
    # 阶梯类（需要额外实现）
    "annual_usage": "annual_usage",
    "current_tier": "current_tier",
    "tier_price": "tier_price",
}

# === 阶梯气价配置 ===
# 与旧版 zr-gas-ha 配置兼容
TIERED_PRICING = {
    "tier1_threshold": 0,       # 第一档起始量 (m³)
    "tier2_threshold": 400,      # 第二档起始量 (m³)
    "tier3_threshold": 1680,     # 第三档起始量 (m³)
    "tier1_price": 2.99,        # 第一档单价 (元/m³)
    "tier2_price": 3.44,        # 第二档单价 (元/m³)
    "tier3_price": 4.34,        # 第三档单价 (元/m³)
    "cycle_start_month": "01",   # 阶梯周期起始月份
    "cycle_start_day": "01",    # 阶梯周期起始日期
}

# 错误码映射
ERROR_CODES = {
    "10000": "成功",
    "10001": "系统错误",
    "10002": "参数错误",
    "20001": "用户未登录",
    "20002": "Token无效",
    "20003": "Token过期",
    "30001": "账户不存在",
    "30002": "账户已绑定",
    "40001": "验证码错误",
    "40002": "验证码过期",
}
