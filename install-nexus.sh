#!/bin/bash
set -e

CHECK_MARK="\033[1;32m✔\033[0m"
CROSS_MARK="\033[1;31m✘\033[0m"
YELLOW_TEXT="\033[1;33m"
GREEN_TEXT="\033[1;32m"
BLUE_TEXT="\033[1;34m"
RED_TEXT="\033[1;31m"
RESET_TEXT="\033[0m"

# 配置文件路径
NEXUS_CONFIG_DIR="$HOME/.nexus"
NODE_ID_FILE="$NEXUS_CONFIG_DIR/node_id"
SCREEN_SESSION="nexus"

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

# 显示标题
echo_blue "
███    ██ ███████ ██   ██ ██    ██ ███████ 
████   ██ ██       ██ ██  ██    ██ ██      
██ ██  ██ █████     ███   ██    ██ ███████ 
██  ██ ██ ██       ██ ██  ██    ██      ██ 
██   ████ ███████ ██   ██  ██████  ███████ 

Nexus Network 安装和管理脚本
"

# 创建配置目录
create_config_dir() {
    if [ ! -d "$NEXUS_CONFIG_DIR" ]; then
        mkdir -p "$NEXUS_CONFIG_DIR"
        echo -e "[配置目录] 已创建 $NEXUS_CONFIG_DIR $CHECK_MARK"
    else
        echo -e "[配置目录] 已存在 $CHECK_MARK"
    fi
}

# 检查 nexus-cli 是否已安装
check_nexus_installation() {
    if command -v nexus-cli &> /dev/null; then
        local version=$(nexus-cli --version 2>/dev/null || echo "unknown")
        echo -e "[Nexus CLI] 已安装 (版本: $version) $CHECK_MARK"
        return 0
    else
        echo -e "[Nexus CLI] 未安装 $CROSS_MARK"
        return 1
    fi
}

# 安装 Nexus CLI
install_nexus() {
    echo_yellow "正在下载并安装 Nexus CLI..."
    echo_yellow "安装过程中会提示是否继续，请输入 'y' 确认安装"
    
    # 使用 expect 自动化输入 'y'
    if command -v expect &> /dev/null; then
        expect -c "
            spawn bash -c \"curl https://cli.nexus.xyz/ | sh\"
            expect \"Do you want to continue?*\" { send \"y\r\" }
            expect eof
        "
    else
        echo_yellow "未找到 expect 命令，将进行手动安装"
        echo_yellow "请在提示时输入 'y' 来确认安装"
        curl https://cli.nexus.xyz/ | sh
    fi
    
    # 检查安装是否成功
    if command -v nexus-cli &> /dev/null; then
        echo -e "[Nexus CLI] 安装成功 $CHECK_MARK"
        
        # 添加到 PATH（如果需要）
        local shell_config=""
        if [[ "$SHELL" == */zsh ]]; then
            shell_config="$HOME/.zshrc"
        elif [[ "$SHELL" == */bash ]]; then
            shell_config="$HOME/.bashrc"
        else
            shell_config="$HOME/.profile"
        fi
        
        # 检查是否需要添加 nexus 到 PATH
        if [ -f "$shell_config" ] && ! grep -q "nexus" "$shell_config"; then
            echo 'export PATH="$HOME/.nexus:$PATH"' >> "$shell_config"
            echo -e "[环境变量] 已添加到 $shell_config $CHECK_MARK"
        fi
    else
        echo -e "[Nexus CLI] 安装失败 $CROSS_MARK"
        echo_red "请手动运行以下命令进行安装："
        echo_red "curl https://cli.nexus.xyz/ | sh"
        exit 1
    fi
}

# 获取或设置 Node ID
get_or_set_node_id() {
    if [ -f "$NODE_ID_FILE" ]; then
        NODE_ID=$(cat "$NODE_ID_FILE")
        echo -e "[Node ID] 已保存: $NODE_ID $CHECK_MARK"
    else
        echo_yellow "首次运行，需要设置 Node ID"
        echo_yellow "请输入您的 Node ID："
        read -p "Node ID: " NODE_ID
        
        if [ -z "$NODE_ID" ]; then
            echo_red "Node ID 不能为空"
            exit 1
        fi
        
        # 保存 Node ID
        echo "$NODE_ID" > "$NODE_ID_FILE"
        echo -e "[Node ID] 已保存到 $NODE_ID_FILE $CHECK_MARK"
    fi
}

# 检查 screen 是否可用
check_screen() {
    if ! command -v screen &> /dev/null; then
        echo_red "未找到 screen 命令，请先安装 screen："
        echo_red "brew install screen"
        exit 1
    fi
}

# 检查 Nexus 进程是否运行
check_nexus_process() {
    if pgrep -f "nexus-cli.*start" > /dev/null; then
        return 0  # 运行中
    else
        return 1  # 未运行
    fi
}

# 检查 screen 会话是否存在
check_screen_session() {
    if screen -list | grep -q "$SCREEN_SESSION"; then
        return 0  # 存在
    else
        return 1  # 不存在
    fi
}

# 启动 Nexus 在 screen 会话中
start_nexus() {
    echo_green "启动 Nexus Network..."
    
    # 检查是否已有运行中的进程
    if check_nexus_process; then
        echo_yellow "Nexus 进程已在运行中"
        if check_screen_session; then
            echo_yellow "可以使用 'screen -r $SCREEN_SESSION' 连接到会话"
        fi
        return 0
    fi
    
    # 清理可能存在的死会话
    if check_screen_session; then
        echo_yellow "清理已存在的 screen 会话..."
        screen -S "$SCREEN_SESSION" -X quit 2>/dev/null || true
        sleep 2
    fi
    
    # 创建新的 screen 会话并启动 nexus
    echo_green "在 screen 会话中启动 Nexus..."
    screen -dmS "$SCREEN_SESSION" bash -c "nexus-cli start --node-id $NODE_ID; exec bash"
    
    # 等待进程启动
    sleep 3
    
    # 验证启动状态
    if check_nexus_process; then
        echo -e "[Nexus Network] 启动成功 $CHECK_MARK"
        echo_green "使用以下命令管理 Nexus："
        echo_green "  - screen -r $SCREEN_SESSION  # 连接到会话"
        echo_green "  - Ctrl+A, D                 # 从会话中分离"
        echo_green "  - screen -list               # 查看所有会话"
    else
        echo -e "[Nexus Network] 启动失败 $CROSS_MARK"
        echo_red "请检查 screen 会话状态: screen -r $SCREEN_SESSION"
        exit 1
    fi
}

# 停止 Nexus
stop_nexus() {
    echo_yellow "停止 Nexus Network..."
    
    # 终止进程
    if check_nexus_process; then
        pkill -f "nexus-cli.*start"
        echo -e "[Nexus Network] 进程已停止 $CHECK_MARK"
    else
        echo_yellow "Nexus 进程未运行"
    fi
    
    # 清理 screen 会话
    if check_screen_session; then
        screen -S "$SCREEN_SESSION" -X quit 2>/dev/null || true
        echo -e "[Screen 会话] 已清理 $CHECK_MARK"
    fi
}

# 显示状态
show_status() {
    echo_blue "=== Nexus Network 状态 ==="
    
    # 检查安装状态
    if check_nexus_installation; then
        local version=$(nexus-cli --version 2>/dev/null || echo "unknown")
        echo_green "✓ Nexus CLI: 已安装 (版本: $version)"
    else
        echo_red "✗ Nexus CLI: 未安装"
    fi
    
    # 检查 Node ID
    if [ -f "$NODE_ID_FILE" ]; then
        local saved_id=$(cat "$NODE_ID_FILE")
        echo_green "✓ Node ID: $saved_id"
    else
        echo_red "✗ Node ID: 未设置"
    fi
    
    # 检查进程状态
    if check_nexus_process; then
        echo_green "✓ Nexus 进程: 运行中"
        local pids=$(pgrep -f "nexus-cli.*start")
        echo_green "  PID: $pids"
    else
        echo_red "✗ Nexus 进程: 未运行"
    fi
    
    # 检查 screen 会话
    if check_screen_session; then
        echo_green "✓ Screen 会话: 存在 ($SCREEN_SESSION)"
    else
        echo_red "✗ Screen 会话: 不存在"
    fi
    
    echo_blue "=========================="
}

# 主菜单
show_menu() {
    echo_blue "
=== Nexus Network 管理菜单 ===
1. 安装 Nexus CLI
2. 设置/更新 Node ID
3. 启动 Nexus Network
4. 停止 Nexus Network
5. 查看状态
6. 连接到 Screen 会话
7. 退出
============================="
}

# 主程序
main() {
    # 创建配置目录
    create_config_dir
    
    # 检查 screen
    check_screen
    
    # 如果没有参数，显示菜单
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "请选择操作 (1-7): " choice
            
            case $choice in
                1)
                    if ! check_nexus_installation; then
                        install_nexus
                    else
                        echo_yellow "Nexus CLI 已安装"
                    fi
                    ;;
                2)
                    echo_yellow "设置新的 Node ID（当前ID将被覆盖）："
                    read -p "Node ID: " NEW_NODE_ID
                    if [ -n "$NEW_NODE_ID" ]; then
                        echo "$NEW_NODE_ID" > "$NODE_ID_FILE"
                        echo -e "[Node ID] 已更新 $CHECK_MARK"
                    fi
                    ;;
                3)
                    if ! check_nexus_installation; then
                        echo_red "请先安装 Nexus CLI"
                        continue
                    fi
                    get_or_set_node_id
                    start_nexus
                    ;;
                4)
                    stop_nexus
                    ;;
                5)
                    show_status
                    ;;
                6)
                    if check_screen_session; then
                        echo_green "连接到 screen 会话..."
                        screen -r "$SCREEN_SESSION"
                    else
                        echo_red "Screen 会话不存在"
                    fi
                    ;;
                7)
                    echo_green "退出程序"
                    exit 0
                    ;;
                *)
                    echo_red "无效选择，请输入 1-7"
                    ;;
            esac
            
            echo
            read -p "按 Enter 继续..."
            clear
        done
    fi
    
    # 处理命令行参数
    case "$1" in
        "install")
            if ! check_nexus_installation; then
                install_nexus
            else
                echo_yellow "Nexus CLI 已安装"
            fi
            ;;
        "start")
            if ! check_nexus_installation; then
                echo_red "请先运行: $0 install"
                exit 1
            fi
            get_or_set_node_id
            start_nexus
            ;;
        "stop")
            stop_nexus
            ;;
        "status")
            show_status
            ;;
        "connect")
            if check_screen_session; then
                screen -r "$SCREEN_SESSION"
            else
                echo_red "Screen 会话不存在"
                exit 1
            fi
            ;;
        *)
            echo_yellow "用法: $0 [install|start|stop|status|connect]"
            echo_yellow "或直接运行 $0 进入交互式菜单"
            exit 1
            ;;
    esac
}

# 运行主程序
main "$@"