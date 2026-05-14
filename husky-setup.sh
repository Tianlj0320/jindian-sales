#!/usr/bin/env bash
# ── 初始化 Git Hooks — 只需运行一次 ────────────────
# 用法：bash husky-setup.sh

set -e

echo '==> 初始化 Husky...'
npx husky init

echo ''
echo '==> 安装 commitlint 依赖...'
npm install --save-dev @commitlint/cli @commitlint/config-conventional

echo ''
echo '==> 写入 pre-commit hook...'
cat > .husky/pre-commit << 'EOF'
#!/usr/bin/env sh
. "$(dirname "$0")/_/husky.sh"

# 提交前检查：仅对暂存文件运行 lint-staged
npx --no-install lint-staged || {
  echo '❌ 提交前检查失败，请修复后重试'
  echo '  运行 npm run lint:fix 自动修复，或 git commit --no-verify 跳过检查'
  exit 1
}
EOF

echo ''
echo '==> 写入 commit-msg hook...'
cat > .husky/commit-msg << 'EOF'
#!/usr/bin/env sh
. "$(dirname "$0")/_/husky.sh"

# 提交信息规范检查
npx --no-install commitlint --edit "$1" || {
  echo '❌ 提交信息不符合规范'
  echo '  格式：type(scope): subject'
  echo '  示例：feat(orders): 添加异常回滚功能'
  exit 1
}
EOF

chmod +x .husky/pre-commit .husky/commit-msg

echo ''
echo '✅ 完成！Husky hooks 已配置成功'
echo '   现在可以执行: git add . && git commit -m "chore: 初始化开发工具链"'
