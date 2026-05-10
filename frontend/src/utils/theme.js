/**
 * 主题管理工具
 *
 * 样式分层架构：
 *   基底样式  /themes/base.css       — 布局、字体、间距、圆角（所有主题共用）
 *   配色主题  /themes/theme{1-7}.css  — 仅颜色变量和组件配色（动态切换）
 *
 * base.css 在 index.html 同步加载，theme.css 动态切换
 * 持久化到 localStorage
 */

const THEME_KEY = 'app-theme'
const THEME_NAMES = {
  theme1: '墨绿/茶色',
  theme2: '暖檀/棕茶色',
  theme3: '竹青/水墨色',
  theme4: '经典蓝白',
  theme5: '秋枫/暖橙色',
  theme6: '烟霞/暮紫色',
  theme7: '沧海/蔚蓝色',
}

function getSavedTheme() {
  return localStorage.getItem(THEME_KEY) || 'theme1'
}

function getThemeLabel(themeId) {
  return THEME_NAMES[themeId] || themeId
}

function getAllThemes() {
  return Object.entries(THEME_NAMES).map(([id, label]) => ({ id, label }))
}

function applyTheme(themeId) {
  let link = document.getElementById('theme-css')
  if (!link) {
    link = document.createElement('link')
    link.rel = 'stylesheet'
    link.id = 'theme-css'
    document.head.appendChild(link)
  }
  link.href = `/themes/${themeId}.css`
  localStorage.setItem(THEME_KEY, themeId)
}

/**
 * 在页面渲染前同步加载已保存的主题（用于 index.html 内联脚本）
 * 返回主题 id，供 JS 层后续使用
 */
function preloadTheme() {
  const id = localStorage.getItem(THEME_KEY)
  if (id && ['theme1', 'theme2', 'theme3'].includes(id)) {
    document.write(`<link rel="stylesheet" id="theme-css" href="/themes/${id}.css">`)
    return id
  }
  document.write('<link rel="stylesheet" id="theme-css" href="/themes/theme1.css">')
  return 'theme1'
}

// 默认导出供 Vue 组件使用
export default {
  THEME_KEY,
  getSavedTheme,
  getThemeLabel,
  getAllThemes,
  applyTheme,
  preloadTheme,
}
