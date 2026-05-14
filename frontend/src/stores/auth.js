import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '[]'))

  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => user.value?.name || '')

  /** 检查当前用户是否拥有指定权限（* 表示拥有全部） */
  function hasPermission(perm) {
    const perms = permissions.value
    if (perms.includes('*')) return true
    return perms.includes(perm)
  }

  async function login(username, password) {
    const res = await authApi.login({ username, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    // 登录后加载权限
    await loadPermissions()
    return res
  }

  async function loadPermissions() {
    try {
      const res = await authApi.permissions()
      permissions.value = res.data?.permissions || []
      localStorage.setItem('permissions', JSON.stringify(permissions.value))
    } catch {
      permissions.value = []
      localStorage.removeItem('permissions')
    }
  }

  async function fetchUser() {
    try {
      const res = await authApi.me()
      user.value = res.data
      localStorage.setItem('user', JSON.stringify(res.data))
      await loadPermissions()
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = {}
    permissions.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('permissions')
  }

  return { token, user, permissions, isLoggedIn, userName, hasPermission, login, loadPermissions, fetchUser, logout }
})
