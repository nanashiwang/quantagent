<template>
  <div class="page-shell">
    <section class="page-hero page-hero--compact">
      <span class="page-eyebrow">Data Source Access</span>
      <h2>Tushare 配置</h2>
      <p>同时维护 Tushare 接入参数与行情数据拉取策略，让连接、调度和展示走同一套配置。</p>
    </section>

    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="panel-toolbar">
          <div class="panel-toolbar__copy">
            <div class="panel-title">连接参数</div>
            <div class="panel-subtitle">用于校验 Tushare 授权和自定义网关，影响所有行情调用入口。</div>
          </div>
          <span class="section-tag">Tushare Pro</span>
        </div>
      </template>

      <el-form :model="connectionForm" label-width="120px" class="settings-form">
        <el-form-item label="Token">
          <el-input
            v-model="connectionForm.token"
            type="password"
            show-password
            :placeholder="tokenPlaceholder"
          />
        </el-form-item>

        <el-form-item label="API URL">
          <el-input
            v-model="connectionForm.api_url"
            placeholder="http://121.40.135.59:8010/"
          />
          <div class="settings-tip">
            如果你的接入方式需要设置 <code>pro._DataApi__http_url</code>，请在这里填写对应地址。
          </div>
        </el-form-item>

        <el-form-item>
          <div class="settings-actions">
            <el-button type="primary" @click="saveConnectionSettings" :loading="connectionSaving">
              保存连接配置
            </el-button>
            <el-button @click="testConnection" :loading="testing">
              测试连接
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <el-alert
        v-if="testResult"
        :title="testResult.message"
        :type="testResult.success ? 'success' : 'error'"
        show-icon
      />
    </el-card>

    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="panel-toolbar">
          <div class="panel-toolbar__copy">
            <div class="panel-title">行情拉取策略</div>
            <div class="panel-subtitle">决定拉哪些股票、拉什么信息、多久自动同步一次，以及回看多少天历史数据。</div>
          </div>
          <span class="section-tag">Sync Policy</span>
        </div>
      </template>

      <el-form :model="marketForm" label-width="120px" class="settings-form">
        <el-form-item label="股票池">
          <el-input
            v-model="marketForm.symbols"
            type="textarea"
            :rows="4"
            placeholder="000001.SZ,600519.SH,159915.SZ"
          />
          <div class="settings-tip">支持英文逗号、中文逗号或换行分隔，建议先从 3 到 10 只核心标的开始。</div>
        </el-form-item>

        <el-form-item label="拉取信息">
          <el-checkbox-group v-model="marketForm.data_types" class="checkbox-grid">
            <el-checkbox v-for="item in datasetOptions" :key="item.value" :label="item.value">
              {{ item.label }}
            </el-checkbox>
          </el-checkbox-group>
          <div class="settings-tip">日线行情适合画图，基础指标和资金流向适合表格分析，龙虎榜适合事件补充。</div>
        </el-form-item>

        <div class="settings-grid">
          <el-form-item label="同步频率(秒)">
            <el-input-number v-model="marketForm.fetch_interval" :min="60" :step="300" />
          </el-form-item>

          <el-form-item label="历史天数">
            <el-input-number v-model="marketForm.history_days" :min="1" :step="5" />
          </el-form-item>

          <el-form-item label="自动同步">
            <el-switch v-model="marketForm.auto_sync" />
          </el-form-item>
        </div>

        <el-form-item>
          <div class="settings-actions">
            <el-button type="primary" @click="saveMarketSettings" :loading="marketSaving">
              保存拉取策略
            </el-button>
            <el-button type="success" @click="runSyncNow" :loading="syncing">
              立即同步一次
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <div class="runtime-grid">
        <div class="runtime-card glass-surface">
          <span>最近同步时间</span>
          <strong>{{ runtimeStatus.last_sync_at || '尚未执行' }}</strong>
        </div>
        <div class="runtime-card glass-surface">
          <span>最近同步状态</span>
          <strong>{{ runtimeStatus.last_sync_status || '未开始' }}</strong>
        </div>
        <div class="runtime-card glass-surface runtime-card--message">
          <span>最近同步说明</span>
          <strong>{{ runtimeStatus.last_sync_message || '保存策略后可手动同步，也可以开启自动同步。' }}</strong>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { syncMarketData } from '../../api/index'
import { getSettings, testTushare, updateSettings } from '../../api/settings'

const datasetOptions = [
  { label: '日线行情', value: 'daily' },
  { label: '基础指标', value: 'daily_basic' },
  { label: '资金流向', value: 'moneyflow' },
  { label: '龙虎榜', value: 'top_list' },
]

const connectionForm = ref({ token: '', api_url: '' })
const marketForm = ref({
  symbols: '',
  data_types: ['daily', 'daily_basic', 'moneyflow'],
  fetch_interval: 3600,
  history_days: 30,
  auto_sync: false,
})
const runtimeStatus = ref({
  last_sync_at: '',
  last_sync_status: '',
  last_sync_message: '',
})
const connectionSaving = ref(false)
const marketSaving = ref(false)
const testing = ref(false)
const syncing = ref(false)
const testResult = ref(null)
const tokenPlaceholder = ref('Tushare Pro Token')

function getErrorMessage(error, fallback) {
  return error?.response?.data?.detail || error?.response?.data?.message || error?.message || fallback
}

function parseBoolean(value) {
  return ['1', 'true', 'yes', 'on'].includes(String(value || '').trim().toLowerCase())
}

function parseInteger(value, fallback) {
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) ? parsed : fallback
}

function parseList(value, fallback = []) {
  if (!value) {
    return fallback
  }
  return String(value)
    .replaceAll('\n', ',')
    .replaceAll('，', ',')
    .split(',')
    .map(item => item.trim())
    .filter(Boolean)
}

function buildConnectionSettingsPayload() {
  return {
    settings: [
      { key: 'token', value: connectionForm.value.token, is_secret: true },
      { key: 'api_url', value: connectionForm.value.api_url, is_secret: false },
    ],
  }
}

function buildMarketSettingsPayload() {
  return {
    settings: [
      { key: 'symbols', value: marketForm.value.symbols, is_secret: false },
      { key: 'data_types', value: marketForm.value.data_types.join(','), is_secret: false },
      { key: 'fetch_interval', value: String(marketForm.value.fetch_interval), is_secret: false },
      { key: 'history_days', value: String(marketForm.value.history_days), is_secret: false },
      { key: 'auto_sync', value: String(marketForm.value.auto_sync), is_secret: false },
    ],
  }
}

async function loadConnectionSettings() {
  const res = await getSettings('tushare')
  const tokenSetting = res.settings.find(item => item.key === 'token')
  const apiUrlSetting = res.settings.find(item => item.key === 'api_url')

  if (tokenSetting) {
    if (tokenSetting.value && tokenSetting.value.includes('****')) {
      tokenPlaceholder.value = `${tokenSetting.value}（已保存，如需更换请重新输入）`
      connectionForm.value.token = ''
    } else {
      connectionForm.value.token = tokenSetting.value
    }
  }

  if (apiUrlSetting) {
    connectionForm.value.api_url = apiUrlSetting.value || ''
  }
}

async function loadMarketSettings() {
  const res = await getSettings('market_data')
  const map = Object.fromEntries((res.settings || []).map(item => [item.key, item.value]))
  marketForm.value.symbols = map.symbols || ''
  marketForm.value.data_types = parseList(map.data_types, ['daily', 'daily_basic', 'moneyflow'])
  marketForm.value.fetch_interval = parseInteger(map.fetch_interval, 3600)
  marketForm.value.history_days = parseInteger(map.history_days, 30)
  marketForm.value.auto_sync = parseBoolean(map.auto_sync)
}

async function loadRuntimeSettings() {
  const res = await getSettings('market_data_runtime')
  const map = Object.fromEntries((res.settings || []).map(item => [item.key, item.value]))
  runtimeStatus.value = {
    last_sync_at: map.last_sync_at || '',
    last_sync_status: map.last_sync_status || '',
    last_sync_message: map.last_sync_message || '',
  }
}

async function saveConnectionSettings() {
  connectionSaving.value = true
  try {
    await updateSettings('tushare', buildConnectionSettingsPayload())
    ElMessage.success('连接配置已保存')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '保存失败'))
  } finally {
    connectionSaving.value = false
  }
}

async function saveMarketSettings() {
  marketSaving.value = true
  try {
    await updateSettings('market_data', buildMarketSettingsPayload())
    ElMessage.success('拉取策略已保存')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '保存失败'))
  } finally {
    marketSaving.value = false
  }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    testResult.value = await testTushare({
      token: connectionForm.value.token,
      api_url: connectionForm.value.api_url,
    })
  } catch (error) {
    testResult.value = { success: false, message: getErrorMessage(error, '请求失败') }
  } finally {
    testing.value = false
  }
}

async function runSyncNow() {
  syncing.value = true
  try {
    await updateSettings('market_data', buildMarketSettingsPayload())
    const result = await syncMarketData()
    ElMessage.success(result.message || '同步完成')
    await loadRuntimeSettings()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '同步失败'))
  } finally {
    syncing.value = false
  }
}

onMounted(async () => {
  try {
    await Promise.all([
      loadConnectionSettings(),
      loadMarketSettings(),
      loadRuntimeSettings(),
    ])
  } catch {}
})
</script>

<style scoped>
.settings-form {
  max-width: 980px;
}

.settings-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.settings-tip {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
}

.runtime-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.runtime-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px;
}

.runtime-card span {
  color: var(--text-secondary);
  font-size: 12px;
}

.runtime-card strong {
  line-height: 1.6;
}

.runtime-card--message {
  grid-column: span 1;
}

@media (max-width: 960px) {
  .settings-grid,
  .runtime-grid,
  .checkbox-grid {
    grid-template-columns: 1fr;
  }
}
</style>
