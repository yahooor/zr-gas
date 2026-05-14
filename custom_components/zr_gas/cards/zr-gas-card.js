/**
 * 中燃在线燃气卡片
 * 显示燃气余额、用量、费用等数据
 *
 * 使用方法:
 * type: custom:zr-gas-card
 * entity: sensor.zr_gas_xxxx_balance
 * -或-
 * type: custom:zr-gas-card
 * entities:
 *   - sensor.zr_gas_xxxx_balance
 *   - sensor.zr_gas_xxxx_monthly_usage
 *   - sensor.zr_gas_xxxx_monthly_cost
 */

const CARD_VERSION = '0.12.2';

class ZrGasCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity && !config.entities) {
      throw new Error('请配置 entity 或 entities');
    }

    this.config = config;
    this._hass = null;
    this.attachShadow({ mode: 'open' });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  static get styles() {
    return `
      :host {
        display: block;
        background: var(--card-background-color, #fff);
        border-radius: 12px;
        padding: 16px;
        box-shadow: var(--card-box-shadow, 0 2px 8px rgba(0,0,0,0.1));
      }
      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--card-border-color, #e0e0e0);
      }
      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color, #212121);
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .card-icon {
        width: 24px;
        height: 24px;
        color: #ff6b35;
      }
      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4caf50;
      }
      .status-dot.offline {
        background: #f44336;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 12px;
      }
      .item {
        text-align: center;
        padding: 12px 8px;
        background: var(--card-secondary-background-color, #f5f5f5);
        border-radius: 8px;
      }
      .item-label {
        font-size: 12px;
        color: var(--secondary-text-color, #757575);
        margin-bottom: 4px;
      }
      .item-value {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color, #212121);
      }
      .item-value.balance {
        color: #4caf50;
      }
      .item-value.balance.negative {
        color: #f44336;
      }
      .item-value.owe {
        color: #ff9800;
      }
      .item-unit {
        font-size: 12px;
        color: var(--secondary-text-color, #757575);
        font-weight: normal;
      }
      .row {
        display: flex;
        justify-content: space-between;
        margin-top: 8px;
      }
      .row-item {
        flex: 1;
        text-align: center;
        padding: 8px;
      }
      .info-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-top: 1px solid var(--card-border-color, #eee);
        margin-top: 8px;
        font-size: 12px;
        color: var(--secondary-text-color, #757575);
      }
      .warning {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px;
        background: #fff3e0;
        border-radius: 8px;
        color: #e65100;
        font-size: 14px;
        margin-top: 12px;
      }
      .warning-icon {
        width: 20px;
        height: 20px;
      }
      .footer {
        display: flex;
        justify-content: space-between;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--card-border-color, #e0e0e0);
        font-size: 11px;
        color: var(--secondary-text-color, #9e9e9e);
      }
    `;
  }

  _render() {
    const entity = this.config.entity || this.config.entities?.[0];
    const title = this.config.title || '中燃在线';

    this.shadowRoot.innerHTML = `
      <style>${ZrGasCard.styles()}</style>
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <svg class="card-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 11v7c0 1.1.9 2 2 2h2v-5.07c0-2.21 1.79-4 4-4 1.1 0 2 .9 2 2v5.07h2c1.1 0 2-.9 2-2v-7l-3.21-2.79c.13.58.21 1.17.21 1.79 0 4.08-3.05 7.44-7 7.93z"/>
            </svg>
            ${title}
          </div>
          <div class="status-dot" title="在线"></div>
        </div>
        <div class="grid" id="grid">
          <div class="item">
            <div class="item-label">账户余额</div>
            <div class="item-value balance" id="balance">--</div>
          </div>
          <div class="item">
            <div class="item-label">月度用量</div>
            <div class="item-value" id="monthly_usage">--<span class="item-unit"> m³</span></div>
          </div>
          <div class="item">
            <div class="item-label">月度费用</div>
            <div class="item-value" id="monthly_cost">--<span class="item-unit"> 元</span></div>
          </div>
          <div class="item">
            <div class="item-label">欠费金额</div>
            <div class="item-value owe" id="owe_money">--<span class="item-unit"> 元</span></div>
          </div>
          <div class="item">
            <div class="item-label">表读数</div>
            <div class="item-value" id="meter_reading">--<span class="item-unit"> m³</span></div>
          </div>
          <div class="item">
            <div class="item-label">气量余额</div>
            <div class="item-value" id="gas_balance">--<span class="item-unit"> m³</span></div>
          </div>
          <div class="item">
            <div class="item-label">燃气单价</div>
            <div class="item-value" id="gas_price">--<span class="item-unit"> 元/m³</span></div>
          </div>
          <div class="item">
            <div class="item-label">购气次数</div>
            <div class="item-value" id="purch_times">--<span class="item-unit"> 次</span></div>
          </div>
        </div>
        <div class="warning" id="warning" style="display:none;">
          <svg class="warning-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
          </svg>
          <span id="warning-text"></span>
        </div>
        <div class="info-row">
          <span id="cust_code">客户编号: --</span>
          <span id="meter_no">燃气表: --</span>
        </div>
        <div class="footer">
          <span>中燃在线 v${CARD_VERSION}</span>
          <span id="last_update">最后更新: --</span>
        </div>
      </div>
    `;
  }

  _update() {
    if (!this._hass) return;

    const entities = this.config.entities || [this.config.entity];
    const states = entities.map(e => this._hass.states[e]).filter(s => s);

    if (states.length === 0) return;

    // 主要实体
    const mainState = states[0];

    // 更新余额
    const balance = this._getState('sensor.zr_gas', 'balance');
    if (balance !== null) {
      const balanceEl = this.shadowRoot.getElementById('balance');
      if (balanceEl) {
        const val = parseFloat(balance.state) || 0;
        balanceEl.textContent = `¥${val.toFixed(2)}`;
        balanceEl.classList.toggle('negative', val < 0);
      }
    }

    // 更新月度用量
    const monthlyUsage = this._getState('sensor.zr_gas', 'monthly_usage');
    if (monthlyUsage) {
      const el = this.shadowRoot.getElementById('monthly_usage');
      if (el) {
        const val = parseFloat(monthlyUsage.state) || 0;
        el.innerHTML = `${val.toFixed(2)}<span class="item-unit"> m³</span>`;
      }
    }

    // 更新月度费用
    const monthlyCost = this._getState('sensor.zr_gas', 'monthly_cost');
    if (monthlyCost) {
      const el = this.shadowRoot.getElementById('monthly_cost');
      if (el) {
        const val = parseFloat(monthlyCost.state) || 0;
        el.innerHTML = `¥${val.toFixed(2)}<span class="item-unit"> 元</span>`;
      }
    }

    // 更新欠费金额
    const oweMoney = this._getState('sensor.zr_gas', 'owed_amount') || this._getState('sensor.zr_gas', 'owe_money');
    if (oweMoney) {
      const el = this.shadowRoot.getElementById('owe_money');
      if (el) {
        const val = parseFloat(oweMoney.state) || 0;
        if (val > 0) {
          el.innerHTML = `¥${val.toFixed(2)}<span class="item-unit"> 元</span>`;
          el.classList.add('owe');
        } else {
          el.textContent = '¥0.00';
        }
      }
    }

    // 更新表读数
    const meterReading = this._getState('sensor.zr_gas', 'meter_reading');
    if (meterReading) {
      const el = this.shadowRoot.getElementById('meter_reading');
      if (el) {
        const val = parseFloat(meterReading.state) || 0;
        el.innerHTML = `${val.toFixed(2)}<span class="item-unit"> m³</span>`;
      }
    }

    // 更新气量余额
    const gasBalance = this._getState('sensor.zr_gas', 'gas_balance');
    if (gasBalance) {
      const el = this.shadowRoot.getElementById('gas_balance');
      if (el) {
        const val = parseFloat(gasBalance.state) || 0;
        el.innerHTML = `${val.toFixed(2)}<span class="item-unit"> m³</span>`;
      }
    }

    // 更新燃气单价
    const gasPrice = this._getState('sensor.zr_gas', 'gas_price');
    if (gasPrice) {
      const el = this.shadowRoot.getElementById('gas_price');
      if (el) {
        const val = parseFloat(gasPrice.state) || 0;
        el.innerHTML = `¥${val.toFixed(2)}<span class="item-unit"> 元/m³</span>`;
      }
    }

    // 更新购气次数
    const purchTimes = this._getState('sensor.zr_gas', 'purch_times') || this._getState('sensor.zr_gas', 'purchase_count');
    if (purchTimes) {
      const el = this.shadowRoot.getElementById('purch_times');
      if (el) {
        el.textContent = purchTimes.state;
      }
    }

    // 获取实体属性
    const attrs = mainState.attributes || {};

    // 更新客户编号
    const custCodeEl = this.shadowRoot.getElementById('cust_code');
    if (custCodeEl && attrs.cust_code) {
      custCodeEl.textContent = `客户编号: ${attrs.cust_code}`;
    }

    // 更新燃气表号
    const meterNoEl = this.shadowRoot.getElementById('meter_no');
    if (meterNoEl && attrs.meter_no) {
      meterNoEl.textContent = `燃气表: ${attrs.meter_no}`;
    }

    // 更新最后抄表时间
    const lastRecordTime = attrs.last_record_time;
    if (lastRecordTime) {
      const timeEl = this.shadowRoot.getElementById('last_update');
      if (timeEl) {
        timeEl.textContent = `最后更新: ${lastRecordTime}`;
      }
    }

    // 检查欠费警告
    const owe = parseFloat(oweMoney?.state || 0);
    const balanceVal = parseFloat(balance?.state || 0);
    const warningEl = this.shadowRoot.getElementById('warning');
    const warningTextEl = this.shadowRoot.getElementById('warning-text');

    if (warningEl && warningTextEl) {
      if (owe > 0) {
        warningTextEl.textContent = `提醒: 您已欠费 ¥${owe.toFixed(2)} 元，请及时充值`;
        warningEl.style.display = 'flex';
      } else if (balanceVal < 50 && balanceVal >= 0) {
        warningTextEl.textContent = `提醒: 余额不足 ¥${balanceVal.toFixed(2)} 元，请及时充值`;
        warningEl.style.display = 'flex';
      } else {
        warningEl.style.display = 'none';
      }
    }

    // 检查在线状态
    const statusDot = this.shadowRoot.querySelector('.status-dot');
    if (statusDot) {
      const diagnostic = this._getState('sensor.zr_gas', 'diagnostic');
      const isOnline = diagnostic?.state === '在线';
      statusDot.classList.toggle('offline', !isOnline);
      statusDot.title = isOnline ? '在线' : '离线';
    }
  }

  _getState(domain, suffix) {
    if (!this._hass) return null;
    const entityId = Object.keys(this._hass.states)
      .find(id => id.startsWith(`sensor.${domain}_`) && id.endsWith(suffix));
    return entityId ? this._hass.states[entityId] : null;
  }
}

customElements.define('zr-gas-card', ZrGasCard);