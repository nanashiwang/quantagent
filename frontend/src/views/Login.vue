<template>
  <div class="login-page">
    <div class="login-bg-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>

    <div class="login-card">
      <div class="login-brand">
        <div class="brand-icon">QA</div>
        <h2>QuantAgent</h2>
        <p class="brand-sub">量化交易协同控制台</p>
      </div>

      <div class="mode-switch">
        <button
          type="button"
          class="mode-switch__item"
          :class="{ 'is-active': mode === 'login' }"
          @click="switchMode('login')"
        >
          登录
        </button>
        <button
          type="button"
          class="mode-switch__item"
          :class="{ 'is-active': mode === 'register' }"
          @click="switchMode('register')"
        >
          注册
        </button>
      </div>

      <div class="mode-copy">
        <h3>{{ mode === 'login' ? '欢迎回来' : '创建新账号' }}</h3>
        <p>
          {{
            mode === 'login'
              ? '登录后可继续查看推荐、回测和行情数据。'
              : '注册成功后会自动登录，并直接进入个人中心，方便你修改用户名和密码。'
          }}
        </p>
      </div>

      <el-form
        v-if="mode === 'login'"
        :model="loginForm"
        @submit.prevent="handleLogin"
        label-position="top"
        class="login-form"
      >
        <el-form-item>
          <el-input v-model="loginForm.username" placeholder="请输入用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <div class="login-options">
          <div class="login-options__group">
            <el-checkbox v-model="loginForm.rememberMe" @change="auth.setRememberPreference">
              记住我
            </el-checkbox>
            <el-checkbox
              v-model="loginForm.rememberUsername"
              @change="(value) => auth.setRememberUsernamePreference(value, loginForm.username)"
            >
              记住用户名
            </el-checkbox>
          </div>
          <span class="login-options__tip">下次打开浏览器自动保持登录</span>
        </div>
        <el-button type="primary" native-type="submit" :loading="loading" size="large" class="login-btn">
          {{ loading ? '登录中...' : '立即登录' }}
        </el-button>
      </el-form>

      <el-form
        v-else
        :model="registerForm"
        @submit.prevent="handleRegister"
        label-position="top"
        class="login-form"
      >
        <el-form-item>
          <el-input v-model="registerForm.username" placeholder="请输入用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请设置密码，至少 6 位"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" size="large" class="login-btn">
          {{ loading ? '注册中...' : '注册并进入系统' }}
        </el-button>
      </el-form>

      <p class="hint">
        {{
          mode === 'login'
            ? '没有账号？点击上方“注册”即可创建普通用户。'
            : '注册后的账号默认为普通用户，如需管理员权限请由管理员在后台授权。'
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'

import { login, register as registerUser } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const mode = ref('login')
const loading = ref(false)
const loginForm = ref({
  username: auth.rememberedUsername || '',
  password: '',
  rememberMe: auth.rememberMe,
  rememberUsername: auth.rememberUsername,
})
const registerForm = ref({ username: '', password: '', confirmPassword: '' })

function switchMode(nextMode) {
  mode.value = nextMode
}

function resetRegisterForm() {
  registerForm.value = { username: '', password: '', confirmPassword: '' }
}

async function handleLogin() {
  if (!loginForm.value.username.trim() || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    const res = await login({
      username: loginForm.value.username.trim(),
      password: loginForm.value.password,
      remember_me: loginForm.value.rememberMe,
    })
    auth.setAuth(res, {
      rememberMe: loginForm.value.rememberMe,
      rememberUsername: loginForm.value.rememberUsername,
      username: loginForm.value.username.trim(),
    })
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const username = registerForm.value.username.trim()
  const password = registerForm.value.password
  const confirmPassword = registerForm.value.confirmPassword

  if (!username) {
    ElMessage.warning('请输入用户名')
    return
  }

  if (!password) {
    ElMessage.warning('请输入密码')
    return
  }

  if (password.length < 6) {
    ElMessage.warning('密码长度不能少于 6 位')
    return
  }

  if (password !== confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    await registerUser({ username, password })
    const loginRes = await login({
      username,
      password,
      remember_me: loginForm.value.rememberMe,
    })
    auth.setAuth(loginRes, {
      rememberMe: loginForm.value.rememberMe,
      rememberUsername: loginForm.value.rememberUsername,
      username,
    })
    resetRegisterForm()
    loginForm.value = {
      username,
      password: '',
      rememberMe: loginForm.value.rememberMe,
      rememberUsername: loginForm.value.rememberUsername,
    }
    ElMessage.success('注册成功，已自动登录')
    router.push('/profile')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #0a1628 0%, #1a2942 100%);
}

.login-bg-shapes {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
  animation: float 22s ease-in-out infinite;
}

.shape-1 {
  top: -140px;
  right: -100px;
  width: 500px;
  height: 500px;
  background: #0066ff;
}

.shape-2 {
  left: -100px;
  bottom: -100px;
  width: 400px;
  height: 400px;
  background: #00d4aa;
  animation-delay: -8s;
}

.shape-3 {
  top: 45%;
  left: 46%;
  width: 320px;
  height: 320px;
  background: #ff9f40;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(32px, -28px) scale(1.06);
  }
  66% {
    transform: translate(-20px, 22px) scale(0.94);
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: min(480px, calc(100vw - 32px));
  padding: 48px 40px 36px;
  border-radius: var(--radius-2xl);
  border: 1.5px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 32px 96px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  animation: card-enter 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.login-brand {
  margin-bottom: 24px;
  text-align: center;
}

.brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin: 0 auto 18px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #0066ff, #00d4aa);
  color: #fff;
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 0.03em;
  box-shadow: 0 12px 32px rgba(0, 102, 255, 0.4);
}

.login-brand h2 {
  margin: 0 0 8px;
  color: #fafcff;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.brand-sub {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 14px;
  font-weight: 500;
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 6px;
  margin-bottom: 20px;
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.08);
}

.mode-switch__item {
  height: 44px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: rgba(255, 255, 255, 0.75);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition-base);
}

.mode-switch__item:hover {
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.9);
}

.mode-switch__item.is-active {
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.95), rgba(0, 212, 170, 0.92));
  color: #fff;
  box-shadow: 0 8px 20px rgba(0, 102, 255, 0.3);
  transform: translateY(-1px);
}

.mode-copy {
  margin-bottom: 20px;
}

.mode-copy h3 {
  margin: 0 0 10px;
  color: #fafcff;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.mode-copy p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  line-height: 1.65;
  font-size: 14px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: var(--radius-md);
  border: 1.5px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: none !important;
  transition: all var(--transition-base);
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.14);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(0, 212, 170, 0.6);
  background: rgba(255, 255, 255, 0.16);
  box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.1) !important;
}

.login-form :deep(.el-input__inner) {
  color: #fff;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.34);
}

.login-form :deep(.el-input__prefix .el-icon),
.login-form :deep(.el-input__suffix .el-icon) {
  color: rgba(255, 255, 255, 0.42);
}

.login-btn {
  width: 100%;
  height: 50px;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #0066ff, #00d4aa);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.01em;
  transition: all var(--transition-base);
  box-shadow: 0 8px 24px rgba(0, 102, 255, 0.35);
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0, 102, 255, 0.45);
}

.login-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 16px rgba(0, 102, 255, 0.4);
}

.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: -2px 2px 18px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
}

.login-options__group {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.login-options :deep(.el-checkbox__label) {
  color: rgba(255, 255, 255, 0.88);
  font-weight: 500;
}

.login-options :deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #fafcff;
  font-weight: 600;
}

.login-options__tip {
  color: rgba(255, 255, 255, 0.52);
  font-size: 12px;
}

.hint {
  margin: 20px 0 0;
  color: rgba(255, 255, 255, 0.48);
  text-align: center;
  font-size: 13px;
  line-height: 1.65;
}
</style>
