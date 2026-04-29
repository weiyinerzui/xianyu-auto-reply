#!/bin/bash
# 阿里云轻量服务器系统调优脚本
# 运行方法: sudo chmod +x system-tuning.sh && sudo ./system-tuning.sh

set -e
echo "=== 阿里云轻量服务器系统调优 ==="

# 1. 配置 swap 行为
echo "[1/4] 配置 swap 参数..."
if ! grep -q "vm.swappiness=10" /etc/sysctl.conf; then
    cat >> /etc/sysctl.conf << 'EOF'
# Xianyu Auto Reply 优化
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.dirty_ratio=10
vm.dirty_background_ratio=5
EOF
    sysctl -p
    echo "  ✓ swap 参数已配置"
else
    echo "  ✓ swap 参数已存在"
fi

# 2. 配置 Docker 日志轮转
echo "[2/4] 配置 Docker 日志轮转..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
systemctl restart docker || true
echo "  ✓ Docker 日志轮转已配置"

# 3. 清理缓存
echo "[3/4] 清理系统缓存..."
docker system prune -f 2>/dev/null || true
sync && echo 3 > /proc/sys/vm/drop_caches
echo "  ✓ 系统缓存已清理"

# 4. 检查 swap 状态
echo "[4/4] 检查系统状态..."
echo ""
echo "=== Swap 状态 ==="
swapon -s || echo "无 swap 分区"
echo ""
echo "=== 内存状态 ==="
free -h
echo ""
echo "=== 调优完成 ==="
