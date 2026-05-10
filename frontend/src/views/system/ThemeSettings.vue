<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h3>主题切换</h3>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom:24px">
        <template #title>
          选择系统界面配色方案，切换后立即生效并自动保存。
        </template>
      </el-alert>

      <div class="theme-grid">
        <div
          v-for="t in themes"
          :key="t.id"
          class="theme-card"
          :class="{ active: currentTheme === t.id }"
          @click="handleSwitch(t.id)"
        >
          <div class="theme-preview" :style="previewStyle(t.id)">
            <div class="preview-sidebar" :style="{ background: t.sidebarColor }"></div>
            <div class="preview-main">
              <div class="preview-header" :style="{ borderBottomColor: t.primaryColor }"></div>
              <div class="preview-content">
                <div class="preview-btn" :style="{ background: t.primaryColor }"></div>
                <div class="preview-line" v-for="i in 3" :key="i" :style="{ background: t.lineColor }"></div>
              </div>
            </div>
          </div>
          <div class="theme-label">
            <span>{{ t.label }}</span>
            <el-tag v-if="currentTheme === t.id" size="small" type="success" effect="dark">当前</el-tag>
          </div>
          <div class="theme-colors">
            <span class="color-dot" v-for="c in t.colors" :key="c" :style="{ background: c }"></span>
          </div>
          <div class="theme-desc">{{ t.desc }}</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import theme from '@/utils/theme'

const currentTheme = ref('theme1')

const themes = [
  {
    id: 'theme4',
    label: '经典蓝白',
    desc: 'Element Plus 默认配色，清爽经典',
    primaryColor: '#409EFF',
    sidebarColor: '#001529',
    lineColor: '#E4E7ED',
    colors: ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C'],
  },
  {
    id: 'theme1',
    label: '墨绿/茶色',
    desc: '自然稳重，适合家居软装行业',
    primaryColor: '#3C6E47',
    sidebarColor: '#1E3525',
    lineColor: '#E4EBE6',
    colors: ['#3C6E47', '#8B7D4E', '#67A85E', '#A8C9A0'],
  },
  {
    id: 'theme2',
    label: '暖檀/棕茶色',
    desc: '温暖雅致，偏成熟商务感',
    primaryColor: '#8B6F47',
    sidebarColor: '#2E2318',
    lineColor: '#E8E0D6',
    colors: ['#8B6F47', '#C49B47', '#C0AA85', '#DACCB5'],
  },
  {
    id: 'theme3',
    label: '竹青/水墨色',
    desc: '清冷素雅，偏中式水墨风格',
    primaryColor: '#4A7B5C',
    sidebarColor: '#1C2E24',
    lineColor: '#DDE8E0',
    colors: ['#4A7B5C', '#B8944A', '#8FB49E', '#BAD0C2'],
  },
  {
    id: 'theme5',
    label: '秋枫/暖橙色',
    desc: '温暖活力，秋日枫叶色调',
    primaryColor: '#D4733B',
    sidebarColor: '#2E1E14',
    lineColor: '#EDE2D8',
    colors: ['#D4733B', '#E8A25E', '#E8B08C', '#D4A24B'],
  },
  {
    id: 'theme6',
    label: '烟霞/暮紫色',
    desc: '优雅别致，烟霞暮色格调',
    primaryColor: '#7A5EA7',
    sidebarColor: '#241B33',
    lineColor: '#E2DAE8',
    colors: ['#7A5EA7', '#9B80C4', '#B5A2CE', '#C49B5E'],
  },
  {
    id: 'theme7',
    label: '沧海/蔚蓝色',
    desc: '深邃宁静，海洋蓝绿色调',
    primaryColor: '#2D7D8A',
    sidebarColor: '#142B30',
    lineColor: '#D8E3E6',
    colors: ['#2D7D8A', '#4DA6B5', '#7EB2BC', '#C49B55'],
  },
]

function previewStyle(themeId) {
  const t = themes.find(x => x.id === themeId)
  if (!t) return {}
  return {
    '--preview-primary': t.primaryColor,
    '--preview-sidebar': t.sidebarColor,
    '--preview-line': t.lineColor,
  }
}

function handleSwitch(id) {
  theme.applyTheme(id)
  currentTheme.value = id
  document.documentElement.setAttribute('data-theme', id)
  ElMessage.success(`已切换至「${theme.getThemeLabel(id)}」主题`)
}

onMounted(() => {
  currentTheme.value = theme.getSavedTheme()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-header h3 { font-size: 18px; margin: 0; }

.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.theme-card {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.25s ease;
  background: #fff;
}
.theme-card:hover {
  border-color: #c0c4cc;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.theme-card.active {
  border-color: var(--preview-primary, #3C6E47);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--preview-primary, #3C6E47) 25%, transparent);
}

.theme-preview {
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  border: 1px solid #ebeef5;
}
.preview-sidebar {
  width: 50px;
  background: var(--preview-sidebar, #1E3525);
}
.preview-main {
  flex: 1;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}
.preview-header {
  height: 24px;
  background: #fff;
  border-bottom: 3px solid var(--preview-primary, #3C6E47);
}
.preview-content {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.preview-btn {
  width: 60px;
  height: 16px;
  border-radius: 3px;
  background: var(--preview-primary, #3C6E47);
}
.preview-line {
  height: 6px;
  border-radius: 3px;
  background: var(--preview-line, #e4e7ed);
  width: 80%;
}

.theme-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}
.theme-colors {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}
.color-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.08);
}
.theme-desc {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}
</style>
