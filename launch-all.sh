#!/bin/bash

# RL Swarm 一键启动脚本
# 自动启动4个窗口：训练 + 监控的完整工作环境

# 颜色定义
GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
PURPLE="\033[1;35m"
RESET="\033[0m"

# 项目路径 - 使用 HOME 环境变量自动适配用户
PROJECT_DIR="$HOME/rl-swarm"

echo -e "${BLUE}🚀 RL Swarm 一键启动脚本${RESET}"
echo -e "${BLUE}=========================${RESET}"

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ 项目目录不存在: $PROJECT_DIR${RESET}"
    exit 1
fi

# 检查必要的脚本文件
check_scripts() {
    local scripts=("run_rl_swarm.sh" "auto-run.sh" "auto-nexus.sh")
    for script in "${scripts[@]}"; do
        if [ ! -f "$PROJECT_DIR/$script" ]; then
            echo -e "${RED}❌ 脚本文件不存在: $script${RESET}"
            exit 1
        fi
    done
    echo -e "${GREEN}✅ 所有必要脚本文件检查完成${RESET}"
}

# 启动完整工作环境
launch_full_environment() {
    echo -e "${PURPLE}🎯 启动 RL Swarm 完整工作环境...${RESET}"
    echo ""
    
    # 计算窗口大小 (2x2 布局)
    local window_width=640
    local window_height=360
    
    echo -e "${YELLOW}📋 启动顺序：${RESET}"
    echo "  1. 🤖 Gensyn 训练会话"
    echo "  2. 📊 Gensyn 监控会话" 
    echo "  3. 🌐 Nexus 运行会话"
    echo "  4. 📈 Nexus 监控会话"
    echo ""
    
    # 窗口1: Gensyn 训练会话
    echo -e "${GREEN}🤖 启动 Gensyn 训练会话...${RESET}"
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '🤖 启动 Gensyn 训练会话...' && echo '正在连接或创建 gensyn screen 会话...' && screen -r gensyn 2>/dev/null || (echo '创建新的 gensyn 会话...' && screen -S gensyn)"
    set bounds of front window to {0, 0, $window_width, $window_height}
    set custom title of front window to "🤖 Gensyn Training"
end tell
EOF
    sleep 2
    
    # 窗口2: Gensyn 监控会话
    echo -e "${GREEN}📊 启动 Gensyn 监控会话...${RESET}"
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '📊 启动 Gensyn 监控会话...' && echo '运行 auto-run.sh 监控脚本...' && ./auto-run.sh"
    set bounds of front window to {$window_width, 0, $((window_width*2)), $window_height}
    set custom title of front window to "📊 Gensyn Monitor"
end tell
EOF
    sleep 2
    
    # 窗口3: Nexus 运行会话
    echo -e "${GREEN}🌐 启动 Nexus 运行会话...${RESET}"
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '🌐 启动 Nexus 运行会话...' && echo '正在连接或创建 nexus screen 会话...' && screen -r nexus 2>/dev/null || (echo '创建新的 nexus 会话...' && screen -S nexus)"
    set bounds of front window to {0, $window_height, $window_width, $((window_height*2))}
    set custom title of front window to "🌐 Nexus Node"
end tell
EOF
    sleep 2
    
    # 窗口4: Nexus 监控会话
    echo -e "${GREEN}📈 启动 Nexus 监控会话...${RESET}"
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '📈 启动 Nexus 监控会话...' && echo '运行 auto-nexus.sh 监控脚本...' && ./auto-nexus.sh"
    set bounds of front window to {$window_width, $window_height, $((window_width*2)), $((window_height*2))}
    set custom title of front window to "📈 Nexus Monitor"
end tell
EOF
    
    echo ""
    echo -e "${GREEN}🎉 RL Swarm 完整工作环境启动完成！${RESET}"
}

# 显示使用说明
show_usage_info() {
    echo ""
    echo -e "${PURPLE}📖 使用说明：${RESET}"
    echo -e "${BLUE}窗口布局：${RESET}"
    echo "  ┌─────────────┬─────────────┐"
    echo "  │ 🤖 Gensyn   │ 📊 Gensyn   │"
    echo "  │    训练     │    监控     │"
    echo "  ├─────────────┼─────────────┤"
    echo "  │ 🌐 Nexus    │ 📈 Nexus    │"
    echo "  │   运行      │   监控      │"
    echo "  └─────────────┴─────────────┘"
    echo ""
    echo -e "${YELLOW}💡 操作提示：${RESET}"
    echo "  • 使用 Cmd+Tab 在窗口间切换"
    echo "  • 在训练窗口中运行 ./run_rl_swarm.sh 启动训练"
    echo "  • 在 Nexus 窗口中运行相应的 Nexus 命令"
    echo "  • 监控窗口会自动显示运行状态"
    echo "  • 使用 Ctrl+A, D 从 screen 会话中分离"
    echo "  • 使用 screen -list 查看所有会话"
    echo ""
    echo -e "${YELLOW}🔧 管理命令：${RESET}"
    echo "  screen -r gensyn          # 重新连接 Gensyn 训练会话"
    echo "  screen -r nexus           # 重新连接 Nexus 运行会话"
    echo "  screen -list              # 查看所有 screen 会话"
    echo "  ./workspace-layout.sh     # 重新配置窗口布局"
    echo ""
}

# 显示确认提示
show_confirmation() {
    echo -e "${YELLOW}⚠️  准备启动 RL Swarm 完整工作环境${RESET}"
    echo "这将打开4个终端窗口并启动相应的服务"
    echo ""
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}❌ 启动已取消${RESET}"
        exit 0
    fi
}

# 主程序
main() {
    # 进入项目目录
    cd "$PROJECT_DIR" || exit 1
    
    # 检查脚本文件
    check_scripts
    
    # 显示确认提示
    show_confirmation
    
    # 启动完整工作环境
    launch_full_environment
    
    # 显示使用说明
    show_usage_info
    
    echo -e "${GREEN}✨ 启动完成！开始你的 RL Swarm 训练之旅吧！${RESET}"
}

# 错误处理
trap 'echo -e "\n${RED}❌ 启动过程中发生错误${RESET}"; exit 1' ERR

# 运行主程序
main "$@"