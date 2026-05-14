#!/usr/bin/env sh
. "$(dirname "$0")/_/husky.sh"

# 提交前检查：仅对暂存文件运行 lint-staged
npx --no-install lint-staged || {
  echo '❌ 提交前检查失败，请修复后重试'
  echo '  运行 npm run lint:fix 自动修复，或 git commit --no-verify 跳过检查'
  exit 1
}
