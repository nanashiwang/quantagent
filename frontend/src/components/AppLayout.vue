<template>
  <div class="app-frame">
    <div class="app-glow app-glow--one"></div>
    <div class="app-glow app-glow--two"></div>
    <div class="app-glow app-glow--three"></div>

    <el-container class="layout-shell">
      <el-aside width="286px" class="layout-aside">
        <div class="brand-card glass-surface">
          <div class="brand-mark">QA</div>
          <div class="brand-copy">
            <h2>QuantAgent</h2>
            <p>量化交易协同控制台</p>
          </div>
        </div>

        <div class="aside-caption">Workspace Map</div>

        <div class="aside-nav">
          <el-menu
            ref="menuRef"
            :default-active="route.path"
            :default-openeds="defaultOpenGroups"
            class="side-menu"
            router
            @open="handleMenuOpen"
            @close="handleMenuClose"
          >
            <el-sub-menu v-for="group in navGroups" :key="group.index" :index="group.index">
              <template #title>
                <el-icon><component :is="group.icon" /></el-icon>
                <div class="group-copy">
                  <span>{{ group.title }}</span>
                  <small>{{ group.hint }}</small>
                </div>
                <span class="group-count">{{ group.items.length }}</span>
              </template>
              <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
                <div class="menu-copy">
                  <span>{{ item.label }}</span>
                  <small>{{ item.desc }}</small>
                </div>
              </el-menu-item>
            </el-sub-menu>

            <el-sub-menu v-if="auth.isAdmin" index="admin">
              <template #title>
                <el-icon><Setting /></el-icon>
                <div class="group-copy">
                  <span>系统管理</span>
                  <small>配置、用户与运行审计</small>
                </div>
                <span class="group-count">{{ adminItems.length }}</span>
              </template>
              <el-menu-item v-for="item in adminItems" :key="item.path" :index="item.path">
                <div class="menu-copy">
                  <span>{{ item.label }}</span>
                  <small>{{ item.desc }}</small>
                </div>
              </el-menu-item>
            </el-sub-menu>
          </el-menu>
        </div>
      </el-aside>

      <el-container class="layout-content">
        <el-header class="layout-header">
          <div class="header-copy">
            <div class="header-eyebrow">Quant Command Center</div>
            <h1>{{ currentRouteMeta.title }}</h1>
            <p>{{ currentRouteMeta.description }}</p>
          </div>

          <div class="header-tools">
            <div class="header-pill glass-surface">
              <span>今日节奏</span>
              <strong>{{ todayLabel }}</strong>
            </div>

            <el-dropdown @command="handleCommand">
              <div class="account-pill glass-surface">
                <div class="account-avatar">{{ userInitial }}</div>
                <div class="account-copy">
                  <strong>{{ auth.user?.username || 'Guest' }}</strong>
                  <small>{{ auth.isAdmin ? '拥有系统管理权限' : '浏览与执行权限' }}</small>
                </div>
                <el-icon><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-main class="layout-main">
          <router-view v-slot="{ Component, route: viewRoute }">
            <keep-alive :include="keepAliveRouteNames">
              <component
                :is="Component"
                :key="viewRoute.meta.keepAlive ? String(viewRoute.name || viewRoute.path) : viewRoute.fullPath"
              />
            </keep-alive>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowDown,
  CollectionTag,
  DataAnalysis,
  DataBoard,
  Monitor,
  Operation,
  Setting,
  TrendCharts,
} from '@element-plus/icons-vue'

import { useAuthStore } from '../stores/auth'

const MENU_OPEN_GROUPS_STORAGE_KEY = 'quant-agent-open-menu-groups'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const menuRef = ref(null)

const navGroups = [
  {
    index: 'overview',
    title: '总览入口',
    hint: '先看全局状态，再进入具体动作',
    icon: DataBoard,
    items: [
      { path: '/', label: '指挥台', desc: '系统总览、状态汇总与工作流入口' },
      { path: '/profile', label: '个人中心', desc: '维护账号资料、安全设置与登录偏好' },
    ],
  },
  {
    index: 'execution',
    title: '交易执行',
    hint: '把推荐、执行与成交记录串起来',
    icon: TrendCharts,
    items: [
      { path: '/recommend', label: '推荐看板', desc: '查看候选股、权重与推荐理由' },
      { path: '/trades', label: '交易记录', desc: '录入、核对并追踪真实成交' },
    ],
  },
  {
    index: 'validation',
    title: '策略验证',
    hint: '验证建议是否经得起历史与复盘',
    icon: DataAnalysis,
    items: [
      { path: '/backtest', label: '回测系统', desc: '验证策略在历史区间中的表现' },
      { path: '/review', label: '复盘分析', desc: '沉淀正确与错误决策样本' },
    ],
  },
  {
    index: 'research',
    title: '研究实验',
    hint: '专注建模、因子和实验配置',
    icon: Operation,
    items: [
      { path: '/ml', label: '机器学习实验', desc: '配置特征、标签、模型与调优方式' },
    ],
  },
  {
    index: 'intelligence',
    title: '市场情报',
    hint: '行情、资讯与日度简报集中查看',
    icon: Monitor,
    items: [
      { path: '/market/data', label: '行情数据中心', desc: '查看股票池同步结果、趋势图和指标表格' },
      { path: '/news/articles', label: '资讯列表', desc: '查看自动采集入库的新闻、公告与宏观资讯' },
      { path: '/news/briefs', label: '每日简报', desc: '集中查看系统生成的日度资讯摘要' },
    ],
  },
  {
    index: 'knowledge',
    title: '知识沉淀',
    hint: '把经验沉到可追踪的知识资产',
    icon: CollectionTag,
    items: [
      { path: '/knowledge', label: '知识库', desc: '维护热知识、冷知识与经验规则' },
    ],
  },
]

const adminItems = [
  { path: '/settings/llm', label: 'LLM 配置', desc: '模型接入、Key 与连通性检查' },
  { path: '/settings/tushare', label: 'Tushare 配置', desc: '行情数据授权与检查' },
  { path: '/settings/database', label: '数据库配置', desc: '查看当前数据源与存储连接' },
  { path: '/agents', label: 'Agent 管理', desc: '控制各智能体角色、模型与启停状态' },
  { path: '/sources', label: '资讯源管理', desc: '维护新闻与情报采集源' },
  { path: '/users', label: '用户管理', desc: '管理登录账号与权限范围' },
  { path: '/admin/logs', label: '使用日志', desc: '查看实验、回测与调用记录' },
]

function getStoredOpenGroups() {
  if (typeof window === 'undefined') {
    return []
  }
  try {
    const raw = window.localStorage.getItem(MENU_OPEN_GROUPS_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.filter(item => typeof item === 'string') : []
  } catch {
    return []
  }
}

const openMenuGroups = ref(getStoredOpenGroups())
const keepAliveRouteNames = computed(() =>
  router
    .getRoutes()
    .filter(item => item.meta?.keepAlive && typeof item.name === 'string')
    .map(item => item.name)
)

const routeMeta = {
  '/profile': { title: '个人中心', description: '维护当前账号的登录信息与密码，保证个人凭证始终可控。' },
  '/': { title: '指挥台', description: '把推荐、交易、知识和工作流状态汇聚到一个更清晰的主视图。' },
  '/recommend': { title: '推荐看板', description: '用更直观的方式查看策略结果、权重变化与当日推荐。' },
  '/trades': { title: '交易记录', description: '跟踪真实交易数据，并把执行动作沉淀为可追溯的记录。' },
  '/backtest': { title: '回测系统', description: '快速验证参数区间，帮助策略在上线前更早暴露风险。' },
  '/review': { title: '复盘分析', description: '把正确与错误案例聚合起来，形成更高质量的经验闭环。' },
  '/ml': { title: '机器学习实验', description: '在同一页里选择自变量、因变量、模型与调优方式，并输出预测结果。' },
  '/market/data': { title: '行情数据中心', description: '集中查看自定义股票池的行情、基础指标和资金流向，兼顾趋势图与明细表。' },
  '/news/articles': { title: '资讯列表', description: '汇总自动采集入库的公告、监管、宏观和快讯内容，方便统一检索。' },
  '/news/briefs': { title: '每日简报', description: '按日查看系统生成的资讯摘要，快速把握今日重要事件。' },
  '/knowledge': { title: '知识库', description: '管理模型沉淀出的高价值知识，让判断依据持续积累。' },
  '/settings/llm': { title: 'LLM 配置', description: '集中维护模型供应商、网关地址与调用连通性。' },
  '/settings/tushare': { title: 'Tushare 配置', description: '检查行情数据接入状态，保证策略输入稳定。' },
  '/settings/database': { title: '数据库配置', description: '查看应用当前使用的存储链路与配置来源。' },
  '/agents': { title: 'Agent 管理', description: '统一管理多智能体的提示词、模型配置与启停状态。' },
  '/sources': { title: '资讯源管理', description: '维护新闻采集源，让观察层输入更加稳定可靠。' },
  '/users': { title: '用户管理', description: '维护账号、角色与系统访问边界。' },
  '/admin/logs': { title: '使用日志', description: '查看实验与回测日志，帮助识别更稳定的方法与因子方向。' },
}

function resolveRouteMeta(path) {
  if (path.startsWith('/agents/')) {
    return { title: 'Agent 详情', description: '编辑单个智能体的角色配置与行为策略。' }
  }
  return routeMeta[path] || { title: 'QuantAgent', description: '现代化的多智能体量化交易控制界面。' }
}

const allMenuGroupIndexes = computed(() => {
  const indexes = navGroups.map(group => group.index)
  if (auth.isAdmin) {
    indexes.push('admin')
  }
  return indexes
})

function isMenuItemActive(itemPath, currentPath) {
  if (itemPath === currentPath) {
    return true
  }
  if (itemPath === '/') {
    return currentPath === '/'
  }
  return currentPath.startsWith(`${itemPath}/`)
}

const currentRouteGroup = computed(() => {
  for (const group of navGroups) {
    if (group.items.some(item => isMenuItemActive(item.path, route.path))) {
      return group.index
    }
  }

  if (auth.isAdmin && adminItems.some(item => isMenuItemActive(item.path, route.path))) {
    return 'admin'
  }

  return ''
})

const defaultOpenGroups = computed(() => {
  return normalizeOpenGroups([
    ...openMenuGroups.value,
    ...(currentRouteGroup.value ? [currentRouteGroup.value] : []),
  ])
})

const currentRouteMeta = computed(() => resolveRouteMeta(route.path))
const userInitial = computed(() => (auth.user?.username || 'Q').slice(0, 1).toUpperCase())
const todayLabel = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(new Date())

function normalizeOpenGroups(groups) {
  const validIndexes = new Set(allMenuGroupIndexes.value)
  return Array.from(new Set(groups.filter(group => validIndexes.has(group))))
}

function persistOpenGroups(groups) {
  const normalized = normalizeOpenGroups(groups)
  openMenuGroups.value = normalized
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(MENU_OPEN_GROUPS_STORAGE_KEY, JSON.stringify(normalized))
  }
}

function handleMenuOpen(index) {
  persistOpenGroups([...openMenuGroups.value, index])
}

function handleMenuClose(index) {
  persistOpenGroups(openMenuGroups.value.filter(group => group !== index))
}

function handleCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
    return
  }
  if (command === 'logout') {
    auth.logout()
    router.push('/login')
  }
}

watch(
  () => auth.isAdmin,
  () => {
    persistOpenGroups(openMenuGroups.value)
  },
  { immediate: true }
)

watch(
  () => route.path,
  async () => {
    if (!currentRouteGroup.value) {
      return
    }

    if (!openMenuGroups.value.includes(currentRouteGroup.value)) {
      persistOpenGroups([...openMenuGroups.value, currentRouteGroup.value])
    }

    await nextTick()
    menuRef.value?.open?.(currentRouteGroup.value)
  },
  { immediate: true }
)
</script>

<style scoped>
.app-frame {
  position: relative;
  height: 100vh;
  min-height: 100vh;
  padding: 24px;
  overflow: hidden;
}

.app-glow {
  position: fixed;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.5;
  pointer-events: none;
  animation: float-glow 25s ease-in-out infinite;
}

.app-glow--one {
  width: 400px;
  height: 400px;
  top: -100px;
  right: 10%;
  background: rgba(0, 102, 255, 0.2);
}

.app-glow--two {
  width: 320px;
  height: 320px;
  bottom: 10%;
  left: -60px;
  background: rgba(0, 212, 170, 0.18);
  animation-delay: -8s;
}

.app-glow--three {
  width: 260px;
  height: 260px;
  top: 35%;
  left: 30%;
  background: rgba(255, 159, 64, 0.15);
  animation-delay: -15s;
}

@keyframes float-glow {
  0%, 100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.5;
  }
  33% {
    transform: translate(30px, -30px) scale(1.08);
    opacity: 0.65;
  }
  66% {
    transform: translate(-20px, 25px) scale(0.92);
    opacity: 0.45;
  }
}

.layout-shell {
  position: relative;
  z-index: 1;
  height: calc(100vh - 48px);
  min-height: calc(100vh - 48px);
  border-radius: var(--radius-2xl);
  overflow: hidden;
  background: rgba(250, 252, 255, 0.5);
  border: 1.5px solid rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  box-shadow: 0 32px 96px rgba(50, 77, 108, 0.16);
}

.layout-aside {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  min-height: 0;
  padding: 24px 20px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(8, 20, 35, 0.88), rgba(14, 30, 48, 0.78)),
    rgba(10, 22, 38, 0.6);
  color: #f5f9ff;
  border-right: 1.5px solid rgba(255, 255, 255, 0.08);
}

.brand-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.12);
  border: 1.5px solid rgba(255, 255, 255, 0.16);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transition: all var(--transition-base);
}

.brand-card:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.98), rgba(0, 212, 170, 0.92));
  color: #fff;
  font-weight: 800;
  font-size: 20px;
  letter-spacing: 0.05em;
  box-shadow: 0 8px 20px rgba(0, 102, 255, 0.3);
}

.brand-copy h2 {
  margin: 0;
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.brand-copy p {
  margin: 6px 0 0;
  color: rgba(245, 249, 255, 0.65);
  font-size: 12px;
  font-weight: 500;
}

.aside-caption {
  padding: 4px 10px 0;
  color: rgba(243, 248, 255, 0.48);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.16em;
}

.aside-nav {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.layout-content {
  min-width: 0;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: transparent;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-shrink: 0;
  padding: 26px 30px 0;
  height: auto;
}

.header-copy {
  min-width: 0;
}

.header-eyebrow {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.18em;
}

.header-copy h1 {
  margin: 10px 0 10px;
  font-size: clamp(28px, 3vw, 40px);
  line-height: 1.08;
  letter-spacing: -0.04em;
  font-weight: 800;
  background: linear-gradient(135deg, var(--text-primary), var(--brand-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-copy p {
  margin: 0;
  max-width: 720px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-pill {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 18px;
  min-width: 180px;
  transition: all var(--transition-base);
}

.header-pill:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.header-pill span,
.account-copy small {
  color: var(--text-secondary);
  font-size: 12px;
}

.header-pill strong {
  font-size: 14px;
}

.account-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all var(--transition-base);
}

.account-pill:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.account-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--brand-primary), var(--brand-secondary));
  color: #fff;
  font-weight: 800;
  font-size: 16px;
  box-shadow: 0 6px 16px rgba(0, 102, 255, 0.3);
}

.account-copy {
  display: flex;
  flex-direction: column;
}

.layout-main {
  flex: 1;
  min-height: 0;
  padding: 28px 30px 30px;
  overflow: auto;
  overscroll-behavior: contain;
  background: transparent;
}

.group-copy,
.menu-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.group-copy span,
.menu-copy span {
  font-weight: 700;
}

.group-copy small,
.menu-copy small {
  color: inherit;
  opacity: 0.62;
  font-size: 12px;
}

.group-count {
  margin-left: auto;
  min-width: 26px;
  height: 26px;
  padding: 0 8px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(245, 249, 255, 0.72);
  font-size: 11px;
  font-weight: 700;
}

:deep(.side-menu) {
  border: none;
  background: transparent;
}

:deep(.side-menu .el-sub-menu__title),
:deep(.side-menu .el-menu-item) {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  height: auto;
  min-height: 60px;
  line-height: 1.3;
  margin-bottom: 8px;
  padding: 16px 18px !important;
  border-radius: var(--radius-lg);
  color: rgba(245, 249, 255, 0.85);
  transition: all var(--transition-base);
}

:deep(.side-menu .el-sub-menu__title:hover),
:deep(.side-menu .el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  transform: translateX(3px);
}

:deep(.side-menu .el-sub-menu.is-active > .el-sub-menu__title) {
  background: rgba(255, 255, 255, 0.14);
  color: #ffffff;
  border: 1.5px solid rgba(255, 255, 255, 0.14);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

:deep(.side-menu .el-sub-menu.is-active > .el-sub-menu__title .group-count) {
  background: rgba(255, 255, 255, 0.16);
  color: rgba(255, 255, 255, 0.95);
}

:deep(.side-menu .el-menu-item.is-active) {
  border: 1.5px solid rgba(255, 255, 255, 0.18);
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.92), rgba(0, 212, 170, 0.9));
  color: #ffffff;
  box-shadow:
    0 12px 28px rgba(0, 102, 255, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transform: translateX(5px);
}

:deep(.side-menu .el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: 10px;
  top: 50%;
  width: 4px;
  height: 28px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.98);
  transform: translateY(-50%);
}

:deep(.side-menu .el-menu-item.is-active .menu-copy) {
  padding-left: 10px;
}

:deep(.side-menu .el-menu-item.is-active .menu-copy span) {
  color: #ffffff;
  font-weight: 800;
}

:deep(.side-menu .el-menu-item.is-active .menu-copy small) {
  color: rgba(255, 255, 255, 0.82);
  opacity: 1;
}

:deep(.side-menu .el-sub-menu .el-menu) {
  border: none;
  background: transparent;
}

:deep(.side-menu .el-sub-menu__icon-arrow) {
  color: rgba(243, 248, 255, 0.58);
}

@media (max-width: 1200px) {
  .app-frame {
    padding: 14px;
  }

  .layout-shell {
    border-radius: 26px;
  }

  .layout-aside {
    width: 244px !important;
  }
}

@media (max-width: 960px) {
  .app-frame {
    height: auto;
    overflow: visible;
  }

  .layout-shell {
    flex-direction: column;
    height: auto;
  }

  .layout-aside {
    position: static;
    width: 100% !important;
    height: auto;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .layout-content,
  .layout-main {
    height: auto;
    overflow: visible;
  }

  .layout-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-tools {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .layout-main {
    padding: 22px;
  }
}
</style>
