<template>
  <div class="page-shell">
    <section class="page-hero page-hero--compact">
      <span class="page-eyebrow">Source Control</span>
      <h2>资讯源管理</h2>
      <p>统一维护默认资讯源、采集频率、可信度与解析策略。支持单源抓取测试和全量同步。</p>
    </section>

    <el-card class="panel-card">
      <template #header>
        <div class="panel-header">
          <div>
            <div class="panel-title">资讯源列表</div>
            <div class="panel-subtitle">优先级越高，后续在摘要和推荐流程里的权重越大。</div>
          </div>
          <div class="panel-actions">
            <el-button @click="load">刷新</el-button>
            <el-button type="success" :loading="syncing" @click="handleSync">同步启用源</el-button>
            <el-button type="primary" @click="openCreate">新增资讯源</el-button>
          </div>
        </div>
      </template>

      <el-table :data="sources" v-loading="loading">
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column prop="type" label="类型" width="110">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="150" />
        <el-table-column prop="market" label="市场" width="120" />
        <el-table-column label="可信度" width="100">
          <template #default="{ row }">
            <span>{{ Number(row.credibility || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="100">
          <template #default="{ row }">
            <span>{{ Number(row.priority || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
              {{ row.is_enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_fetched" label="上次抓取" width="180" />
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="success" @click="handleFetch(row.id)">抓取</el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" :title="editingId ? '编辑资讯源' : '新增资讯源'" width="720px">
      <el-form label-position="top" :model="form" class="source-form">
        <div class="source-grid">
          <el-form-item label="名称">
            <el-input v-model="form.name" placeholder="例如：证监会" />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="form.type">
              <el-option label="RSS" value="rss" />
              <el-option label="网页采集" value="crawler" />
              <el-option label="巨潮资讯" value="cninfo" />
              <el-option label="Tushare" value="tushare" />
              <el-option label="RSSHub" value="rsshub" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <el-input v-model="form.category" placeholder="公告 / 监管 / 宏观 / 快讯" />
          </el-form-item>
          <el-form-item label="市场">
            <el-input v-model="form.market" placeholder="A股 / 宏观 / 全市场" />
          </el-form-item>
          <el-form-item label="解析器">
            <el-input v-model="form.parser" placeholder="anchor_list / announcements_api / multi_dataset" />
          </el-form-item>
          <el-form-item label="去重策略">
            <el-select v-model="form.dedup_strategy">
              <el-option label="内容哈希" value="content_hash" />
              <el-option label="URL" value="url" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-input-number v-model="form.priority" :min="0" :max="1" :step="0.1" />
          </el-form-item>
          <el-form-item label="可信度">
            <el-input-number v-model="form.credibility" :min="0" :max="1" :step="0.1" />
          </el-form-item>
          <el-form-item label="抓取间隔（秒）">
            <el-input-number v-model="form.fetch_interval" :min="60" :step="600" />
          </el-form-item>
          <el-form-item label="启用状态">
            <el-switch v-model="form.is_enabled" />
          </el-form-item>
        </div>

        <el-form-item label="配置 JSON">
          <el-input
            v-model="configText"
            type="textarea"
            :rows="10"
            placeholder='{"url":"https://example.com","mode":"anchor_list"}'
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createSource,
  deleteSource,
  fetchSource,
  getSources,
  syncNews,
  updateSource,
} from '../../api/index'

const loading = ref(false)
const saving = ref(false)
const syncing = ref(false)
const showDialog = ref(false)
const editingId = ref(null)
const sources = ref([])
const configText = ref('{}')
const form = ref(createEmptyForm())

function createEmptyForm() {
  return {
    name: '',
    type: 'crawler',
    category: '',
    market: '',
    parser: '',
    dedup_strategy: 'content_hash',
    priority: 0.5,
    credibility: 0.5,
    fetch_interval: 3600,
    is_enabled: true,
  }
}

async function load() {
  loading.value = true
  try {
    sources.value = await getSources()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.value = createEmptyForm()
  configText.value = '{}'
  showDialog.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = {
    name: row.name,
    type: row.type,
    category: row.category || '',
    market: row.market || '',
    parser: row.parser || '',
    dedup_strategy: row.dedup_strategy || 'content_hash',
    priority: Number(row.priority ?? 0.5),
    credibility: Number(row.credibility ?? 0.5),
    fetch_interval: row.fetch_interval || 3600,
    is_enabled: Boolean(row.is_enabled),
  }
  configText.value = JSON.stringify(row.config || {}, null, 2)
  showDialog.value = true
}

async function handleSave() {
  let config
  try {
    config = JSON.parse(configText.value || '{}')
  } catch {
    ElMessage.error('配置 JSON 格式不正确')
    return
  }

  const payload = { ...form.value, config }
  saving.value = true
  try {
    if (editingId.value) {
      await updateSource(editingId.value, payload)
      ElMessage.success('资讯源已更新')
    } else {
      await createSource(payload)
      ElMessage.success('资讯源已添加')
    }
    showDialog.value = false
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  await ElMessageBox.confirm('确认删除该资讯源？')
  await deleteSource(id)
  ElMessage.success('资讯源已删除')
  await load()
}

async function handleFetch(id) {
  try {
    const res = await fetchSource(id)
    if (!res.success) {
      ElMessage.error(res.message || '抓取失败')
      return
    }
    ElMessage.success(`抓取 ${res.count} 条，入库 ${res.inserted} 条，重复 ${res.duplicates} 条`)
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '抓取失败')
  }
}

async function handleSync() {
  syncing.value = true
  try {
    const res = await syncNews()
    const level = res.success ? 'success' : 'warning'
    ElMessage[level](
      `同步 ${res.fetched_sources} 个资讯源，新增 ${res.inserted_articles} 条，重复 ${res.duplicate_articles} 条`
    )
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '同步失败')
  } finally {
    syncing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.panel-actions {
  display: flex;
  gap: 10px;
}

.source-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 900px) {
  .panel-header,
  .panel-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .source-grid {
    grid-template-columns: 1fr;
  }
}
</style>
