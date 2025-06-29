#!/bin/bash

# RL-Swarm 智能启动脚本
# 自动检测网络连接问题，智能选择运行模式
# 增强版：自动修复 Apple Silicon 兼容性问题，网络故障自动降级

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

# 检测网络连接性
check_network_connectivity() {
    echo_blue "🌐 检测网络连接状态..."
    
    # 检测基础网络连接
    if ! ping -c 2 -W 5000 8.8.8.8 >/dev/null 2>&1; then
        echo_red "❌ 基础网络连接失败"
        return 1
    fi
    
    # 检测DHT bootstrap节点连接性
    local bootstrap_ips=("38.101.215.14" "38.101.215.13")
    local bootstrap_ports=("31111" "31222" "30002")
    local connection_success=false
    
    echo_yellow "   检测DHT bootstrap节点连接性..."
    
    for ip in "${bootstrap_ips[@]}"; do
        for port in "${bootstrap_ports[@]}"; do
            if timeout 3 bash -c "</dev/tcp/$ip/$port" 2>/dev/null; then
                echo_green "   ✅ 成功连接到 $ip:$port"
                connection_success=true
                break 2
            else
                echo_yellow "   ⚠️  无法连接到 $ip:$port"
            fi
        done
    done
    
    if [ "$connection_success" = true ]; then
        echo_green "✅ 网络连接正常，可以使用网络模式"
        return 0
    else
        echo_red "❌ DHT bootstrap节点不可用"
        return 1
    fi
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

# 网络模式启动
start_network_mode() {
    echo_green "🌐 启动网络模式 (连接测试网)..."
    
    # 设置自动配置环境变量
    export AUTO_TESTNET="y"
    export AUTO_SWARM="a" 
    export AUTO_HF_HUB="n"
    
    echo_green "   配置: 测试网 + Math swarm + 不推送HF Hub"
    
    # 启动网络模式
    exec bash "./ops/scripts/run_rl_swarm_mac.sh"
}

# 本地模式启动
start_local_mode() {
    echo_yellow "🏠 启动本地模式 (离线训练)..."
    echo_blue "   本地模式优势:"
    echo_blue "   - 不依赖网络连接"
    echo_blue "   - 更稳定的训练环境"
    echo_blue "   - 专注于模型训练本身"
    
    # 启动本地模式
    exec bash "./run_rl_swarm_local.sh"
}

echo -e "\033[38;5;220m"
cat << "EOF"
    🚀 RL-Swarm 智能启动脚本 v2.0
    
    新功能:
    🧠 智能网络检测 - 自动选择最佳运行模式
    🔧 自动修复兼容性问题 - Apple Silicon 优化
    🌐 网络模式 - 连接测试网进行分布式训练  
    🏠 本地模式 - 离线训练，避开网络依赖
    
EOF
echo -e "$RESET_TEXT"

echo_green ">> 🎯 开始智能启动流程..."
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

# 🌐 第三步：网络连接检测
echo_green ">> 🌐 步骤3: 智能网络检测..."

if check_network_connectivity; then
    echo ""
    echo_green ">> 🚀 启动网络模式..."
    echo_yellow ">> 按 Ctrl+C 可以停止训练"
    echo ""
    
    # 检查脚本是否存在
    if [ ! -f "./ops/scripts/run_rl_swarm_mac.sh" ]; then
        echo_red ">> ❌ 错误: 找不到网络模式启动脚本"
        echo_yellow ">> 降级到本地模式..."
        start_local_mode
    else
        start_network_mode
    fi
else
    echo ""
    echo_yellow ">> ⚠️ 网络连接不可用，自动切换到本地模式"
    echo_green ">> 🏠 启动本地模式..."
    echo_yellow ">> 按 Ctrl+C 可以停止训练"
    echo ""
    
    # 检查本地模式脚本是否存在
    if [ ! -f "./run_rl_swarm_local.sh" ]; then
        echo_red ">> ❌ 错误: 找不到本地模式启动脚本"
        echo_yellow ">> 请确保您在 rl-swarm 项目根目录中运行此脚本"
        exit 1
    else
        start_local_mode
    fi
fi 