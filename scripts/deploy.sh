#!/bin/bash
# 快速部署脚本
# 运行方法: chmod +x deploy.sh && ./deploy.sh

set -e
echo "=== Xianyu Auto Reply 轻量服务器部署 ==="

# 检查配置文件
if [ ! -f ".env.lightweight" ]; then
    echo "❌ 错误: 缺少 .env.lightweight 文件"
    exit 1
fi

# 1. 停止旧容器
echo "[1/4] 停止旧容器..."
docker stop xianyu-auto-reply 2>/dev/null || true
docker rm xianyu-auto-reply 2>/dev/null || true

# 2. 备份数据
echo "[2/4] 备份数据..."
if [ -d "./data" ]; then
    BACKUP_DIR="./backups/backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r ./data "$BACKUP_DIR/" 2>/dev/null || true
    echo "  ✓ 数据已备份到 $BACKUP_DIR"
fi

# 3. 清理缓存
echo "[3/4] 清理 Docker 缓存..."
docker system prune -f

# 4. 启动新容器
echo "[4/4] 启动容器..."
docker compose -f docker-compose-lightweight.yml up -d

# 等待启动
echo ""
echo "等待容器启动..."
sleep 10

# 检查状态
echo ""
echo "=== 部署完成 ==="
docker ps | grep xianyu
echo ""
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
echo ""
echo "健康检查: curl http://localhost:8080/health"
