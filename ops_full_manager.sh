#!/bin/bash
#
# RL-Swarm 完整运维管理中心
# 如果需要完整功能，使用这个脚本
#
echo "🚀 启动RL-Swarm完整运维管理中心..."
cd "$(dirname "$0")/ops"
python ops_manager.py 