#!/bin/bash
#
# RL-Swarm 简化运维脚本
# 功能：启动监控 + 异常邮件提醒
#

echo "🚀 启动RL-Swarm监控系统..."
echo "📧 邮件提醒已启用: zhilinchn@126.com"
echo "🌐 监控面板: http://localhost:5000 (如端口冲突会自动切换)"
echo ""

# 切换到ops目录
cd "$(dirname "$0")/ops"

# 先检查Apple Silicon兼容性
echo "🔧 检查Apple Silicon兼容性..."
python fixes/fix_mac_accelerate.py

echo ""
echo "📊 启动实时监控系统..."
echo "   - 自动监控训练状态"
echo "   - 性能异常检测"
echo "   - 邮件告警通知"
echo ""
echo "按 Ctrl+C 停止监控"
echo "=" * 50

# 启动实时监控（包含邮件通知）
python monitoring/real_time_monitor.py 