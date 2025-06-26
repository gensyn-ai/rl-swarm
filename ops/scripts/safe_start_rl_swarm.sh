#!/bin/bash

# RL-Swarm 安全启动脚本
# 防止重复启动，包含内存监控和进程检查

set -euo pipefail

GREEN_TEXT="\033[32m"
BLUE_TEXT="\033[34m"
YELLOW_TEXT="\033[33m"
RED_TEXT="\033[31m"
RESET_TEXT="\033[0m"

echo_green() {
    echo -e "$GREEN_TEXT$1$RESET_TEXT"
}

echo_blue() {
    echo -e "$BLUE_TEXT$1$RESET_TEXT"
}

echo_yellow() {
    echo -e "$YELLOW_TEXT$1$RESET_TEXT"
}

echo_red() {
    echo -e "$RED_TEXT$1$RESET_TEXT"
}

echo -e "\033[38;5;226m"
cat << "EOF"
    🛡️ RL-Swarm 安全启动脚本
    
    安全功能:
    ✅ 进程冲突检测
    ✅ 内存使用监控
    ✅ 自动清理功能
    ✅ 防止重复启动
    
EOF
echo -e "$RESET_TEXT"

# 导入安全检查模块
if [ -f "./ops/scripts/safety_checks.sh" ]; then
    source ./ops/scripts/safety_checks.sh
else
    echo_red "❌ 未找到安全检查模块: ./ops/scripts/safety_checks.sh"
    exit 1
fi

# 主程序
main() {
    # 执行安全检查
    run_safety_checks
    echo ""
    
    # 设置默认环境变量
    export AUTO_TESTNET="${AUTO_TESTNET:-y}"
    export AUTO_SWARM="${AUTO_SWARM:-a}"
    export AUTO_HF_HUB="${AUTO_HF_HUB:-n}"
    
    echo_green ">> 🤖 使用自动配置:"
    echo_green "   - AUTO_TESTNET=$AUTO_TESTNET"
    echo_green "   - AUTO_SWARM=$AUTO_SWARM"
    echo_green "   - AUTO_HF_HUB=$AUTO_HF_HUB"
    echo ""
    
    # 启动训练
    echo_green ">> 🚀 启动 RL-Swarm 训练..."
    exec bash ./ops/scripts/run_rl_swarm_mac.sh
}

# 检查是否在正确的目录中
if [ ! -f "ops/scripts/run_rl_swarm_mac.sh" ]; then
    echo_red "❌ 错误: 请在 rl-swarm 项目根目录中运行此脚本"
    exit 1
fi

# 执行主程序
main "$@" 