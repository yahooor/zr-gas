# 中燃在线（重构版）Home Assistant 集成

[![GitHub Releases](https://img.shields.io/github/v/release/yahooor/zr-gas-wechat)](https://github.com/yahooor/zr-gas-wechat/releases)
[![GitHub License](https://img.shields.io/github/license/yahooor/zr-gas-wechat)](LICENSE)

**中燃在线**燃气数据 Home Assistant 自定义集成，支持余额查询、月度用量、阶梯气价、欠费提醒等功能。

## 功能特性

- ✅ 账户余额实时查询
- ✅ 月度/年度用量统计
- ✅ 阶梯气价计算
- ✅ 欠费金额提醒
- ✅ 手动刷新按钮
- ✅ 设备诊断支持
- ✅ 离线缓存
- ✅ 前端可视化卡片
- ✅ 自动重试机制

## 支持的版本

- Home Assistant **2024.1.0+**
- HACS

## 安装方式

### 方式一：HACS（推荐）

1. 安装 [HACS](https://hacs.xyz/)
2. 在 HACS 中搜索"中燃在线"或添加自定义仓库：
   - Repository: `https://github.com/yahooor/zr-gas-wechat`
   - Category: `Integration`
3. 点击安装

### 方式二：手动安装

将项目复制到 Home Assistant 的 `custom_components` 目录：

```bash
cd custom_components
git clone https://github.com/yahooor/zr-gas-wechat.git zr_gas
```

## 配置方法

### 通过 UI 配置

1. 进入 **设置** → **设备与服务**
2. 点击 **添加集成**
3. 搜索"中燃在线"
4. 按提示完成配置

### 支持的认证方式

1. **Token 导入** - 直接粘贴 access_token 和 user_id
2. **短信登录** - 需要图形验证码 + 短信验证码

## 实体列表

| 实体 | 说明 | 单位 |
|------|------|------|
| `sensor.zr_gas_*_balance` | 账户余额 | CNY |
| `sensor.zr_gas_*_monthly_usage` | 月用量 | m³ |
| `sensor.zr_gas_*_monthly_cost` | 月费用 | CNY |
| `sensor.zr_gas_*_owe_money` | 欠费金额 | CNY |
| `sensor.zr_gas_*_annual_usage` | 年度累计用量 | m³ |
| `sensor.zr_gas_*_annual_cost` | 年度累计费用 | CNY |
| `sensor.zr_gas_*_unit_price` | 当前单价 | CNY/m³ |
| `sensor.zr_gas_*_last_record` | 表读数 | m³ |
| `sensor.zr_gas_*_qty_meter_balance` | 气量余额 | m³ |
| `button.zr_gas_*_refresh` | 刷新按钮 | - |

## 前端卡片

添加到 Lovelace UI：

```yaml
type: custom:zr-gas-card
entity: sensor.zr_gas_xxxx_balance
```

## 高级选项

可在集成选项中调整：

- 刷新间隔（默认 300 秒）
- 余额预警阈值
- 账单查询年数
- 阶梯气价配置

## 更新日志

### v0.12.2
- 添加手动刷新按钮
- 添加设备诊断支持
- 添加离线缓存
- 优化重试机制

## 鸣谢

- 基于中燃在线平台抓包分析
- 参考 [zr-gas-ha](https://github.com/yahooor/zr-gas-ha) 项目

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件