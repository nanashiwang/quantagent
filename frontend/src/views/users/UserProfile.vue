<template>
  <div class="page-shell">
    <section class="page-hero page-hero--compact">
      <span class="page-eyebrow">Account Center</span>
      <h2>个人中心</h2>
      <p>这里维护当前登录账号的用户名与密码。修改时需要校验当前密码，避免误操作影响后续登录。</p>
    </section>

    <section class="profile-grid">
      <el-card class="panel-card">
        <template #header>
          <div>
            <div class="panel-title">账号信息</div>
            <div class="panel-subtitle">可修改用户名，角色和状态仅展示。</div>
          </div>
        </template>

        <el-form label-position="top" :model="form" class="profile-form">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>

          <div class="info-grid">
            <div class="info-item glass-surface">
              <span>当前角色</span>
              <strong>{{ userInfo.role === 'admin' ? '管理员' : '普通用户' }}</strong>
            </div>
            <div class="info-item glass-surface">
              <span>账号状态</span>
              <strong>{{ userInfo.is_active ? '正常' : '已禁用' }}</strong>
            </div>
            <div class="info-item glass-surface">
              <span>创建时间</span>
              <strong>{{ userInfo.created_at || '暂无记录' }}</strong>
            </div>
            <div class="info-item glass-surface">
              <span>最近登录</span>
              <strong>{{ userInfo.last_login || '暂无记录' }}</strong>
            </div>
          </div>
        </el-form>
      </el-card>

      <el-card class="panel-card">
        <template #header>
          <div>
            <div class="panel-title">安全设置</div>
            <div class="panel-subtitle">保存前必须输入当前密码，新密码留空则表示不修改。</div>
          </div>
        </template>

        <el-form label-position="top" :model="form" class="profile-form">
          <el-form-item label="当前密码">
            <el-input v-model="form.current_password" type="password" show-password placeholder="请输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="form.new_password" type="password" show-password placeholder="留空则不修改密码" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="form.confirm_password" type="password" show-password placeholder="再次输入新密码" />
          </el-form-item>

          <div class="action-row">
            <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
            <el-button @click="resetPasswords">清空密码项</el-button>
          </div>
        </el-form>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getCurrentUser, updateProfile } from '../../api/auth'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const saving = ref(false)
const userInfo = ref({
  username: auth.user?.username || '',
  role: auth.user?.role || 'user',
  is_active: Boolean(auth.user?.is_active),
  created_at: auth.user?.created_at || '',
  last_login: auth.user?.last_login || '',
})
const form = ref({
  username: auth.user?.username || '',
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const originalUsername = computed(() => userInfo.value.username || '')

async function loadProfile() {
  const me = await getCurrentUser()
  userInfo.value = me
  form.value.username = me.username
}

function resetPasswords() {
  form.value.current_password = ''
  form.value.new_password = ''
  form.value.confirm_password = ''
}

async function handleSave() {
  const username = form.value.username.trim()
  const newPassword = form.value.new_password.trim()
  const confirmPassword = form.value.confirm_password.trim()
  const usernameChanged = username !== originalUsername.value

  if (!username) {
    ElMessage.warning('用户名不能为空')
    return
  }

  if (!usernameChanged && !newPassword) {
    ElMessage.warning('没有检测到需要保存的修改')
    return
  }

  if (!form.value.current_password) {
    ElMessage.warning('请输入当前密码后再保存')
    return
  }

  if (newPassword && newPassword !== confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  const payload = {
    username,
    current_password: form.value.current_password,
    new_password: newPassword || undefined,
  }

  saving.value = true
  try {
    const res = await updateProfile(payload)
    auth.setAuth(res, {
      rememberMe: auth.rememberMe,
      rememberUsername: auth.rememberUsername,
      username: res.user.username,
    })
    userInfo.value = res.user
    form.value.username = res.user.username
    resetPasswords()
    ElMessage.success('个人信息已更新')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 20px;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px;
}

.info-item span {
  color: var(--text-secondary);
  font-size: 12px;
}

.info-item strong {
  font-size: 15px;
  line-height: 1.5;
  word-break: break-word;
}

.action-row {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

@media (max-width: 1080px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .action-row {
    flex-direction: column;
  }
}
</style>
