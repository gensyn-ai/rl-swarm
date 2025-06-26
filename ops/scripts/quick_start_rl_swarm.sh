#!/bin/bash

# RL-Swarm 快速启动脚本
# 使用默认配置 (连接测试网, Math A swarm, 不推送到HF Hub)
# 增强版：自动检测和修复 Apple Silicon 兼容性问题

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

# 自动检测和修复 accelerate 兼容性问题
auto_fix_accelerate() {
    echo_blue "🔍 检测 accelerate 版本兼容性..."
    
    # 获取当前 accelerate 版本
    local current_version=$(uv pip list | grep accelerate | awk '{print $2}' || echo "not_found")
    
    if [ "$current_version" = "not_found" ]; then
        echo_red "❌ accelerate 未安装"
        return 1
    fi
    
    echo_yellow "   当前版本: accelerate $current_version"
    
    # 检查是否是有问题的版本
    if [ "$current_version" = "1.8.0" ] || [[ "$current_version" =~ ^1\.8\. ]]; then
        echo_red "❌ 检测到有问题的 accelerate 版本: $current_version"
        echo_green "🔧 自动修复：降级到稳定版本 1.7.0..."
        
        if uv pip install accelerate==1.7.0 --force-reinstall --quiet; then
            echo_green "✅ accelerate 已修复到 1.7.0"
            return 0
        else
            echo_red "❌ 自动修复失败"
            return 1
        fi
    else
        echo_green "✅ accelerate 版本正常: $current_version"
        return 0
    fi
}

echo -e "\033[38;5;220m"
cat << "EOF"
    🚀 RL-Swarm 增强快速启动脚本
    
    增强功能:
    ✅ 自动检测和修复 Apple Silicon 兼容性问题
    ✅ 连接到测试网 (Testnet)
    ✅ 加入 Math (A) swarm  
    ✅ 不推送模型到 Hugging Face Hub
    
EOF
echo -e "$RESET_TEXT"

echo_green ">> 🎯 使用默认配置启动 RL-Swarm..."
echo_blue ">> 如需自定义配置，请直接运行: ./ops/scripts/run_rl_swarm_mac.sh"
echo ""

# 🔧 第一步：安全检查
echo_green ">> 🛡️ 步骤1: 执行安全检查..."
if [ -f "./ops/scripts/safety_checks.sh" ]; then
    echo_blue "   导入安全检查模块..."
    source ./ops/scripts/safety_checks.sh
    
    # 执行安全检查
    run_safety_checks
    echo ""
else
    echo_yellow "   ⚠️ 未找到安全检查模块，跳过安全检查..."
fi

# 🔧 第二步：自动修复兼容性问题  
echo_green ">> 🔧 步骤2: 检测和修复兼容性问题..."
if ! auto_fix_accelerate; then
    echo_red ">> ❌ 兼容性修复失败，退出启动"
    exit 1
fi

echo ""
echo_green ">> 🚀 步骤3: 启动训练系统..."

# 设置自动配置环境变量
export AUTO_TESTNET="y"
export AUTO_SWARM="a" 
export AUTO_HF_HUB="n"

echo_green ">> 🤖 自动配置已设置:"
echo_green "   - AUTO_TESTNET=y (连接测试网)"
echo_green "   - AUTO_SWARM=a (Math swarm)"  
echo_green "   - AUTO_HF_HUB=n (不推送到HF Hub)"
echo ""

# 检查脚本是否存在
SCRIPT_PATH="./ops/scripts/run_rl_swarm_mac.sh"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo_red ">> ❌ 错误: 找不到 $SCRIPT_PATH"
    echo_yellow ">> 请确保您在 rl-swarm 项目根目录中运行此脚本"
    exit 1
fi

echo_green ">> 🚀 启动 RL-Swarm..."
echo_yellow ">> 按 Ctrl+C 可以停止训练"
echo ""

# 启动 RL-Swarm
exec bash "$SCRIPT_PATH" 