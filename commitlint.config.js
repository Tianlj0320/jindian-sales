/**
 * Commitlint 配置 — Git 提交信息规范
 *
 * 格式：type(scope): subject
 * 示例：feat(orders): 添加异常回滚功能
 *       fix(purchase): 修复 422 分页错误
 *       style(theme): 更新墨绿配色
 */
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // 新功能
        'fix',      // 修复
        'style',    // 样式/主题变动
        'refactor', // 重构
        'test',     // 测试
        'docs',     // 文档
        'chore',    // 工程化/工具链
        'perf',     // 性能优化
        'ci',       // CI/CD 变动
      ],
    ],
    'scope-case': [2, 'always', 'lower-case'],
    'subject-case': [2, 'never', ['upper-case', 'start-case']],
    'subject-empty': [2, 'never'],
    'type-empty': [2, 'never'],
  },
}
