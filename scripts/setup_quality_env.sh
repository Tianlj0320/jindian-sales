#!/bin/bash
# ========================================
# 金典软装销售系统 · 质量环境初始化脚本
# ========================================
set -e

echo "📦 安装 Python 质量工具..."
pip install ruff mypy pytest pytest-asyncio

echo "🔧 安装 pre-commit hook..."
pip install pre-commit
pre-commit install

echo "✅ 质量工具安装完成！"

echo ""
echo "常用命令："
echo "  ruff check app/          # 检查代码"
echo "  ruff format app/         # 格式化代码"
echo "  mypy app/                # 类型检查"
echo "  pytest tests/            # 运行测试"
echo "  pre-commit run --all-files  # 运行所有 hook"
echo ""
echo "IDE 推荐配置："
echo "  VSCode: 安装 Ruff、Pylance 插件"
echo "  PyCharm: 安装 Ruff 插件 + File Watcher"
