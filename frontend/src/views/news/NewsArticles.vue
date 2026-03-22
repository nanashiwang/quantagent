<template>
  <div class="page-shell">
    <section class="page-hero page-hero--compact">
      <span class="page-eyebrow">News Warehouse</span>
      <h2>资讯列表</h2>
      <p>查看已入库的新闻、公告、监管动态和宏观数据，支持按关键词、来源与日期过滤。</p>
    </section>

    <el-card class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">筛选条件</div>
          <div class="panel-subtitle">默认展示最新 100 条资讯。</div>
        </div>
      </template>

      <div class="filter-grid">
        <el-input v-model="filters.keyword" placeholder="关键词" clearable @keyup.enter="load" />
        <el-select v-model="filters.source_id" clearable placeholder="资讯源">
          <el-option v-for="item in sources" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
        />
        <el-button type="primary" @click="load">查询</el-button>
      </div>
    </el-card>

    <el-card class="panel-card">
      <template #header>
        <div>
          <div class="panel-title">入库资讯</div>
          <div class="panel-subtitle">当前共展示 {{ articles.length }} 条记录。</div>
        </div>
      </template>

      <el-table :data="articles" v-loading="loading">
        <el-table-column label="标题" min-width="360">
          <template #default="{ row }">
            <div class="title-cell">
              <a v-if="row.url" :href="row.url" target="_blank" rel="noreferrer">{{ row.title }}</a>
              <span v-else>{{ row.title }}</span>
              <small>{{ row.summary }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="source_name" label="来源" width="160" />
        <el-table-column prop="source_category" label="分类" width="140" />
        <el-table-column label="标签" width="180">
          <template #default="{ row }">
            <div class="tag-list">
              <el-tag v-for="tag in row.tags.slice(0, 3)" :key="tag" size="small">{{ tag }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="重要性" width="90">
          <template #default="{ row }">
            {{ Number(row.importance || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="published_at" label="发布时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import { getNewsArticles, getSources } from '../../api/index'

const loading = ref(false)
const articles = ref([])
const sources = ref([])
const dateRange = ref([])
const filters = ref({
  keyword: '',
  source_id: null,
})

async function loadSources() {
  sources.value = await getSources()
}

async function load() {
  loading.value = true
  try {
    articles.value = await getNewsArticles({
      keyword: filters.value.keyword,
      source_id: filters.value.source_id || undefined,
      date_from: dateRange.value?.[0] || undefined,
      date_to: dateRange.value?.[1] || undefined,
      limit: 100,
    })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadSources()
  await load()
})
</script>

<style scoped>
.filter-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr 1.2fr auto;
  gap: 14px;
  align-items: center;
}

.title-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-cell a,
.title-cell span {
  color: var(--text-primary);
  font-weight: 700;
  text-decoration: none;
}

.title-cell small {
  color: var(--text-secondary);
  line-height: 1.5;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

@media (max-width: 960px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
