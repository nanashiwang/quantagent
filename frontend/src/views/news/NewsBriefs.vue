<template>
  <div class="page-shell">
    <section class="page-hero page-hero--compact">
      <span class="page-eyebrow">Daily Digest</span>
      <h2>每日简报</h2>
      <p>系统会按天汇总高优先级资讯，帮助你快速把握监管、公告、宏观和快讯的核心变化。</p>
    </section>

    <el-card class="panel-card">
      <template #header>
        <div class="brief-header">
          <div>
            <div class="panel-title">简报列表</div>
            <div class="panel-subtitle">默认展示最近 30 份自动生成的简报。</div>
          </div>
          <el-button @click="load">刷新</el-button>
        </div>
      </template>

      <div class="brief-list" v-loading="loading">
        <article v-for="item in briefs" :key="item.id" class="brief-card glass-surface">
          <div class="brief-meta">
            <span class="section-tag">{{ item.date }}</span>
            <small>{{ item.source || 'news_digest' }}</small>
          </div>
          <pre>{{ item.content }}</pre>
        </article>

        <el-empty v-if="!loading && briefs.length === 0" description="暂时还没有生成简报" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import { getNewsBriefs } from '../../api/index'

const loading = ref(false)
const briefs = ref([])

async function load() {
  loading.value = true
  try {
    briefs.value = await getNewsBriefs({ limit: 30 })
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.brief-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.brief-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.brief-card {
  padding: 22px;
}

.brief-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.brief-meta small {
  color: var(--text-secondary);
}

.brief-card pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  line-height: 1.7;
  color: var(--text-primary);
}

@media (max-width: 960px) {
  .brief-header,
  .brief-meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
