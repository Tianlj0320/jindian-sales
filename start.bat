@echo off
chcp 65001 >nul
echo ====================================
echo   金典软装ERP - 一键启动
echo ====================================

:: 检查前端是否已构建
if not exist "frontend\dist\index.html" (
    echo [1/2] 正在构建前端...
    cd frontend
    call npm run build
    cd ..
    echo 前端构建完成
) else (
    echo [1/2] 前端已构建，跳过
)

echo [2/2] 启动后端服务...
cd backend
python main.py
