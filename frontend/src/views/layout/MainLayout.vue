<template>
  <el-container style="height:100vh">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="router.push('/dashboard')">
        <span v-if="!isCollapse" class="logo-text">金典软装ERP</span>
        <span v-else class="logo-mini">金</span>
      </div>
      <div class="sidebar-menu-wrap">
        <el-menu
        :default-active="route.path"
        :collapse="isCollapse"
        :router="true"
        background-color="#1E3525"
        text-color="#ffffffbf"
        active-text-color="#fff"
      >
        <!-- 工作台 -->
        <el-menu-item v-if="auth.hasPermission('dashboard')" index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>

        <!-- 订单管理 -->
        <el-menu-item v-if="auth.hasPermission('orders')" index="/orders">
          <el-icon><Document /></el-icon>
          <template #title>订单管理</template>
        </el-menu-item>

        <!-- 采购管理 -->
        <el-menu-item v-if="auth.hasPermission('purchases')" index="/purchases">
          <el-icon><ShoppingCart /></el-icon>
          <template #title>采购管理</template>
        </el-menu-item>

        <!-- 仓库管理 -->
        <el-menu-item v-if="auth.hasPermission('warehouse')" index="/warehouse">
          <el-icon><HomeFilled /></el-icon>
          <template #title>仓库管理</template>
        </el-menu-item>

        <!-- 加工单管理 -->
        <el-menu-item v-if="auth.hasPermission('production')" index="/processing">
          <el-icon><SetUp /></el-icon>
          <template #title>加工单管理</template>
        </el-menu-item>

        <!-- 生产反馈 -->
        <el-menu-item v-if="auth.hasPermission('production')" index="/production">
          <el-icon><WarningFilled /></el-icon>
          <template #title>生产反馈</template>
        </el-menu-item>

        <!-- 安装管理 -->
        <el-menu-item v-if="auth.hasPermission('installations')" index="/installations">
          <el-icon><Tools /></el-icon>
          <template #title>安装管理</template>
        </el-menu-item>

        <!-- 售后管理 -->
        <el-menu-item v-if="auth.hasPermission('orders')" index="/after-sales">
          <el-icon><ChatLineRound /></el-icon>
          <template #title>售后管理</template>
        </el-menu-item>

        <!-- 收款管理（原财务管理） -->
        <el-menu-item v-if="auth.hasPermission('finance')" index="/finance">
          <el-icon><Money /></el-icon>
          <template #title>收款管理</template>
        </el-menu-item>

        <!-- 基础资料（分组） -->
        <el-sub-menu v-if="auth.hasPermission('products')||auth.hasPermission('customers')||auth.hasPermission('purchases')||auth.hasPermission('system')||auth.hasPermission('admin')" index="basic">
          <template #title>
            <el-icon><Files /></el-icon>
            <span>基础资料</span>
          </template>
          <el-menu-item v-if="auth.hasPermission('products')" index="/products">
            <el-icon><Goods /></el-icon>
            <template #title>产品管理</template>
          </el-menu-item>
          <el-menu-item v-if="auth.hasPermission('customers')" index="/customers">
            <el-icon><UserFilled /></el-icon>
            <template #title>客户管理</template>
          </el-menu-item>
          <el-menu-item v-if="auth.hasPermission('purchases')" index="/suppliers">
            <el-icon><Van /></el-icon>
            <template #title>供应商管理</template>
          </el-menu-item>
          <el-menu-item v-if="auth.hasPermission('system')" index="/staff">
            <el-icon><User /></el-icon>
            <template #title>员工管理</template>
          </el-menu-item>
          <el-menu-item v-if="auth.hasPermission('admin')" index="/roles">
            <el-icon><Key /></el-icon>
            <template #title>角色权限</template>
          </el-menu-item>
        </el-sub-menu>

        <!-- 日报 -->
        <el-menu-item v-if="auth.hasPermission('reports')" index="/daily-report">
          <el-icon><DataBoard /></el-icon>
          <template #title>日报</template>
        </el-menu-item>

        <!-- 系统设置（分组） -->
        <el-sub-menu v-if="auth.hasPermission('system')||auth.hasPermission('admin')" index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </template>
          <el-menu-item index="/store-settings">
            <el-icon><Shop /></el-icon>
            <template #title>店铺信息</template>
          </el-menu-item>
          <el-menu-item index="/dicts">
            <el-icon><List /></el-icon>
            <template #title>字典管理</template>
          </el-menu-item>
          <el-menu-item index="/logs">
            <el-icon><Tickets /></el-icon>
            <template #title>操作日志</template>
          </el-menu-item>
          <el-menu-item index="/theme-settings">
            <el-icon><MagicStick /></el-icon>
            <template #title>主题切换</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
      </div>
    </el-aside>

    <!-- 主区域 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb>
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ auth.userName }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const isCollapse = ref(false)

function handleCommand(cmd) {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确认退出登录？', '提示').then(() => {
      auth.logout()
      router.push('/login')
    }).catch(() => {})
  }
}
</script>

<style scoped>
.sidebar { background: #1E3525; transition: width 0.3s; overflow: hidden; display: flex; flex-direction: column; }
.logo { height: 60px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.08); }
.logo-text { color: #A8C9A0; font-size: 18px; font-weight: bold; letter-spacing: 3px; }
.logo-mini { color: #A8C9A0; font-size: 20px; font-weight: bold; }
.sidebar-menu-wrap { flex: 1; overflow-y: auto; overflow-x: hidden; }
.sidebar-menu-wrap::-webkit-scrollbar { width: 4px; }
.sidebar-menu-wrap::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }
.el-menu { border-right: none; }
.header { background: #fff; border-bottom: 2px solid #3C6E47; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 60px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.collapse-btn { font-size: 20px; cursor: pointer; color: #606266; }
.header-right .user-info { display: flex; align-items: center; gap: 6px; cursor: pointer; color: #606266; font-size: 14px; }
.main-content { background: #eaf3fb; padding: 20px; overflow-y: auto; }
</style>
