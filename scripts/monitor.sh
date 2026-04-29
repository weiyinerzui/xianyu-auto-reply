#!/bin/bash
# 资源监控脚本
# 运行方法: chmod +x monitor.sh && ./monitor.sh

echo "按 Ctrl+C 退出监控"
sleep 2

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║      Xianyu Auto Reply 资源监控  $(date '+%H:%M:%S')      ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    
    echo "【系统内存】"
    free -h | head -2
    echo ""
    
    echo "【Docker 容器】"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null || echo "无运行中容器"
    echo ""
    
    echo "【最近日志】"
    docker logs --tail 5 xianyu-auto-reply 2>&1 | grep -v "^\s*$" | tail -5 || echo "无日志"
    
    # OOM 检测
    if dmesg 2>/dev/null | tail -30 | grep -qi "out of memory\|oom"; then
        echo ""
        echo "⚠️  警告: 检测到 OOM 事件!"
        dmesg | grep -i "oom" | tail -3
    fi
    
    sleep 5
done
