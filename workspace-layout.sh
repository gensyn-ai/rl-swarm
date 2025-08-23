#!/bin/bash

# RL Swarm 智能多终端布局管理器
# 自动识别屏幕分辨率并创建优化的工作空间布局

# 颜色定义
GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
PURPLE="\033[1;35m"
RESET="\033[0m"

# 项目路径 - 使用 HOME 环境变量自动适配用户
PROJECT_DIR="$HOME/rl-swarm"

echo -e "${BLUE}🚀 RL Swarm 智能工作空间布局器${RESET}"
echo -e "${BLUE}=====================================${RESET}"

# 获取屏幕分辨率
get_screen_resolution() {
    # 获取主屏幕分辨率
    local resolution=$(system_profiler SPDisplaysDataType | grep Resolution | head -n1 | awk '{print $2 "x" $4}')
    echo "$resolution"
}

# 计算窗口位置和大小
calculate_window_layout() {
    local resolution=$1
    local width=$(echo $resolution | cut -d'x' -f1)
    local height=$(echo $resolution | cut -d'x' -f2)
    
    # 计算每个窗口的大小（2x2网格布局）
    local window_width=$((width / 2))
    local window_height=$((height / 2))
    
    echo "窗口尺寸: ${window_width}x${window_height}"
    
    # 定义4个窗口的位置
    declare -A window_positions=(
        ["gensyn"]="0,0,${window_width},${window_height}"
        ["gensyn_monitor"]="${window_width},0,${window_width},${window_height}"
        ["nexus"]="0,${window_height},${window_width},${window_height}"
        ["nexus_monitor"]="${window_width},${window_height},${window_width},${window_height}"
    )
    
    # 输出窗口位置信息（供调试用）
    for window in "${!window_positions[@]}"; do
        echo "  $window: ${window_positions[$window]}"
    done
}

# 创建或连接screen会话
create_or_attach_screen() {
    local session_name=$1
    local command=$2
    
    if screen -list | grep -q "$session_name"; then
        echo -e "${GREEN}✓ 连接到现有会话: $session_name${RESET}"
        echo "screen -r $session_name"
    else
        echo -e "${YELLOW}+ 创建新会话: $session_name${RESET}"
        if [ -n "$command" ]; then
            echo "screen -S $session_name -dm bash -c 'cd $PROJECT_DIR && $command'"
        else
            echo "screen -S $session_name"
        fi
    fi
}

# 布局选择菜单
show_layout_menu() {
    echo -e "${GREEN}选择工作空间布局：${RESET}"
    echo "1. 🎯 完整布局 (4窗口) - 推荐"
    echo "2. 🚀 精简布局 (2窗口) - 仅主要功能"
    echo "3. 📊 监控布局 (2窗口) - 仅监控"
    echo "4. 🛠️  自定义布局"
    echo "5. 📋 显示当前 Screen 会话"
    echo "6. 🔄 重置所有会话"
    echo "7. ❌ 退出"
    echo ""
}

# 完整布局（4窗口）
setup_full_layout() {
    echo -e "${BLUE}🎯 设置完整工作空间布局...${RESET}"
    
    # 2x2 布局
    local window_width=640
    local window_height=360
    
    # 窗口1: Gensyn 训练
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '🤖 Gensyn 训练窗口' && screen -r gensyn 2>/dev/null || screen -S gensyn"
    set bounds of front window to {0, 0, $window_width, $window_height}
    set custom title of front window to "🤖 Gensyn Training"
end tell
EOF

    sleep 1

    # 窗口2: Gensyn 监控
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '📊 Gensyn 监控窗口' && ./auto-run.sh"
    set bounds of front window to {$window_width, 0, $((window_width*2)), $window_height}
    set custom title of front window to "📊 Gensyn Monitor"
end tell
EOF

    sleep 1

    # 窗口3: Nexus 运行
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '🌐 Nexus 运行窗口' && screen -r nexus 2>/dev/null || screen -S nexus"
    set bounds of front window to {0, $window_height, $window_width, $((window_height*2))}
    set custom title of front window to "🌐 Nexus Node"
end tell
EOF

    sleep 1

    # 窗口4: Nexus 监控
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '📈 Nexus 监控窗口' && ./auto-nexus.sh"
    set bounds of front window to {$window_width, $window_height, $((window_width*2)), $((window_height*2))}
    set custom title of front window to "📈 Nexus Monitor"
end tell
EOF

    echo -e "${GREEN}✅ 完整工作空间布局已设置完成！${RESET}"
}

# 精简布局（2窗口）
setup_simple_layout() {
    echo -e "${BLUE}🚀 设置精简布局...${RESET}"
    
    # 左右分布
    local window_width=640
    local window_height=720
    
    # 窗口1: Gensyn 训练
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '🤖 Gensyn 训练窗口' && screen -r gensyn 2>/dev/null || screen -S gensyn"
    set bounds of front window to {0, 0, $window_width, $window_height}
    set custom title of front window to "🤖 Gensyn Training"
end tell
EOF

    sleep 1

    # 窗口2: Nexus 运行
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '🌐 Nexus 运行窗口' && screen -r nexus 2>/dev/null || screen -S nexus"
    set bounds of front window to {$window_width, 0, $((window_width*2)), $window_height}
    set custom title of front window to "🌐 Nexus Node"
end tell
EOF

    echo -e "${GREEN}✅ 精简布局已设置完成！${RESET}"
}

# 监控布局（2窗口）
setup_monitor_layout() {
    echo -e "${BLUE}📊 设置监控布局...${RESET}"
    
    # 左右分布
    local window_width=640
    local window_height=720
    
    # 窗口1: Gensyn 监控
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '📊 Gensyn 监控窗口' && ./auto-run.sh"
    set bounds of front window to {0, 0, $window_width, $window_height}
    set custom title of front window to "📊 Gensyn Monitor"
end tell
EOF

    sleep 1

    # 窗口2: Nexus 监控
    osascript <<EOF
tell application "Terminal"
    do script "cd $PROJECT_DIR && echo '📈 Nexus 监控窗口' && ./auto-nexus.sh"
    set bounds of front window to {$window_width, 0, $((window_width*2)), $window_height}
    set custom title of front window to "📈 Nexus Monitor"
end tell
EOF

    echo -e "${GREEN}✅ 监控布局已设置完成！${RESET}"
}

# 显示当前screen会话
show_screen_sessions() {
    echo -e "${BLUE}📋 当前 Screen 会话状态：${RESET}"
    screen -list
    echo ""
    echo -e "${YELLOW}💡 使用说明：${RESET}"
    echo "  screen -r <session_name>  # 连接会话"
    echo "  Ctrl+A, D                 # 从会话中分离"
    echo "  screen -X -S <session_name> quit  # 结束会话"
}

# 重置所有会话
reset_all_sessions() {
    echo -e "${RED}🔄 重置所有 Screen 会话...${RESET}"
    echo -e "${YELLOW}⚠️  这将结束所有正在运行的训练任务！${RESET}"
    read -p "确定要继续吗？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 结束所有screen会话
        screen -ls | grep Detached | cut -d. -f1 | awk '{print $1}' | xargs -I {} screen -X -S {} quit
        echo -e "${GREEN}✅ 所有会话已重置${RESET}"
    else
        echo -e "${YELLOW}❌ 操作已取消${RESET}"
    fi
}

# 主程序
main() {
    # 检查是否在正确的目录
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}❌ 项目目录不存在: $PROJECT_DIR${RESET}"
        exit 1
    fi
    
    # 获取屏幕分辨率
    resolution=$(get_screen_resolution)
    echo -e "${GREEN}🖥️  检测到屏幕分辨率: $resolution${RESET}"
    echo ""
    
    # 显示菜单
    show_layout_menu
    
    read -p "请选择 (1-7): " choice
    
    case $choice in
        1)
            setup_full_layout
            ;;
        2)
            setup_simple_layout
            ;;
        3)
            setup_monitor_layout
            ;;
        4)
            echo -e "${YELLOW}🛠️  自定义布局功能开发中...${RESET}"
            echo "您可以手动使用 open-screen.sh 脚本创建自定义布局"
            ;;
        5)
            show_screen_sessions
            ;;
        6)
            reset_all_sessions
            ;;
        7)
            echo -e "${GREEN}👋 再见！${RESET}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 无效选择${RESET}"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}🎉 布局设置完成！${RESET}"
    echo -e "${YELLOW}💡 提示：${RESET}"
    echo "  • 使用 Cmd+Tab 在窗口间切换"
    echo "  • 使用 screen -list 查看所有会话"
    echo "  • 使用 ./workspace-layout.sh 重新运行此脚本"
}

# 运行主程序
main "$@"