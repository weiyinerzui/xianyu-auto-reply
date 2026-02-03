#!/bin/bash
set -e

echo "========================================"
echo "  闲鱼自动回复系统 - 启动中..."
echo "========================================"

# 显示环境信息
echo "环境信息："
echo "  - Python版本: $(python --version)"
echo "  - 工作目录: $(pwd)"
echo "  - 时区: ${TZ:-未设置}"
echo "  - 数据库路径: ${DB_PATH:-/app/data/xianyu_data.db}"
echo "  - 日志级别: ${LOG_LEVEL:-INFO}"

# 禁用 core dumps 防止生成 core 文件
ulimit -c 0
echo "✓ 已禁用 core dumps"

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p /app/data /app/logs /app/backups /app/static/uploads/images
mkdir -p /app/trajectory_history
echo "✓ 目录创建完成"

# 启动 Xvfb 虚拟显示器（用于滑块验证的浏览器）
echo "启动 Xvfb 虚拟显示器..."
# 检查是否安装了 xvfb
if command -v Xvfb &> /dev/null; then
    # 先杀掉可能存在的旧进程
    pkill -f "Xvfb :99" 2>/dev/null || true
    # 启动 Xvfb 在 display :99
    Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp &
    export DISPLAY=:99
    sleep 1
    echo "✓ Xvfb 已启动 (DISPLAY=:99)"
else
    echo "⚠ Xvfb 未安装，滑块验证将使用纯 headless 模式"
fi

# 设置目录权限
echo "设置目录权限..."
chmod 777 /app/data /app/logs /app/backups /app/static/uploads /app/static/uploads/images
chmod 777 /app/trajectory_history 2>/dev/null || true
echo "✓ 权限设置完成"

# 检查关键文件
echo "检查关键文件..."
if [ ! -f "/app/global_config.yml" ]; then
    echo "⚠ 警告: 全局配置文件不存在，将使用默认配置"
fi

if [ ! -f "/app/Start.py" ]; then
    echo "✗ 错误: Start.py 文件不存在！"
    exit 1
fi
echo "✓ 关键文件检查完成"

# 检查 Python 依赖
echo "检查 Python 依赖..."
python -c "import fastapi, uvicorn, loguru, websockets" 2>/dev/null || {
    echo "⚠ 警告: 部分 Python 依赖可能未正确安装"
}
echo "✓ Python 依赖检查完成"

# 迁移数据库文件到data目录（如果需要）
echo "检查数据库文件位置..."
if [ -f "/app/xianyu_data.db" ] && [ ! -f "/app/data/xianyu_data.db" ]; then
    echo "发现旧数据库文件，迁移到data目录..."
    mv /app/xianyu_data.db /app/data/xianyu_data.db
    echo "✓ 主数据库已迁移"
elif [ -f "/app/xianyu_data.db" ] && [ -f "/app/data/xianyu_data.db" ]; then
    echo "⚠ 检测到新旧数据库都存在，使用data目录中的数据库"
    echo "  旧文件: /app/xianyu_data.db"
    echo "  新文件: /app/data/xianyu_data.db"
fi

if [ -f "/app/user_stats.db" ] && [ ! -f "/app/data/user_stats.db" ]; then
    echo "迁移统计数据库到data目录..."
    mv /app/user_stats.db /app/data/user_stats.db
    echo "✓ 统计数据库已迁移"
fi

# 迁移备份文件
backup_count=$(ls /app/xianyu_data_backup_*.db 2>/dev/null | wc -l)
if [ "$backup_count" -gt 0 ]; then
    echo "发现 $backup_count 个备份文件，迁移到data目录..."
    mv /app/xianyu_data_backup_*.db /app/data/ 2>/dev/null || true
    echo "✓ 备份文件已迁移"
fi

echo "✓ 数据库文件位置检查完成"

# 显示启动信息
echo "========================================"
echo "  系统启动参数："
echo "  - API端口: ${API_PORT:-8080}"
echo "  - API主机: ${API_HOST:-0.0.0.0}"
echo "  - Debug模式: ${DEBUG:-false}"
echo "  - 自动重载: ${RELOAD:-false}"
echo "========================================"

# 启动应用
echo "正在启动应用..."
echo ""

# 使用 exec 替换当前 shell，这样 Python 进程可以接收信号
exec python Start.py
