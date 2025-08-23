#!/bin/bash

# Nexus节点监控脚本 - 清晰流程版本
# 流程：创建screen会话 -> 在会话中启动nexus -> 监控进程
# 新增：每10分钟检查CPU进程状态，异常时清除会话并重启

# ==================== 配置区域 ====================
# 进程名称（用于查找nexus进程）
PROCESS_NAME="nexus-network"

# Screen会话名称
SCREEN_SESSION="nexus"

# Node ID 配置文件
NEXUS_CONFIG_DIR="$HOME/.nexus"
NODE_ID_FILE="$NEXUS_CONFIG_DIR/node_id"

# 自动读取保存的 Node ID
get_node_id() {
    if [ -f "$NODE_ID_FILE" ]; then
        NODE_ID=$(cat "$NODE_ID_FILE")
        log "🔑 从配置文件读取 Node ID: $NODE_ID"
    else
        log "⚠️  未找到保存的 Node ID，请先运行安装脚本"
        log "请手动输入 Node ID："
        read -p "Node ID: " NODE_ID
        if [ -z "$NODE_ID" ]; then
            log "❌ Node ID 不能为空"
            exit 1
        fi
        # 保存输入的 Node ID
        mkdir -p "$NEXUS_CONFIG_DIR"
        echo "$NODE_ID" > "$NODE_ID_FILE"
        log "✅ Node ID 已保存到 $NODE_ID_FILE"
    fi
}

# 启动命令（动态生成）
get_start_command() {
    get_node_id
    START_CMD="nexus-cli start --node-id $NODE_ID"
    log "🚀 启动命令: $START_CMD"
}

# 监控间隔（秒）- 10分钟
CHECK_INTERVAL=600

# 最大重启次数
MAX_RESTARTS=999

# 日志文件
LOG_FILE="nexus_monitor.log"
# ================================================

# 记录日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查screen是否安装
check_screen() {
    if ! command -v screen > /dev/null 2>&1; then
        log "❌ 错误: 未找到screen命令"
        log "请先安装screen: brew install screen"
        exit 1
    fi
}

# 检查nexus-cli是否安装
check_nexus_cli() {
    if ! command -v nexus-cli > /dev/null 2>&1; then
        log "❌ 错误: 未找到nexus-cli命令"
        log "请先安装 Nexus CLI:"
        log "  curl https://cli.nexus.xyz/ | sh"
        log "安装后请重新运行此脚本"
        log "或手动将 nexus-cli 添加到 PATH 中"
        exit 1
    else
        local nexus_version=$(nexus-cli --version 2>/dev/null || echo "unknown")
        log "✅ nexus-cli 已安装 (版本: $nexus_version)"
    fi
}


# 检查进程状态
check_process() {
    log "🔍 开始检测进程状态..."
    
    # 方法1: 检查真正的nexus-cli进程（不是Screen管理进程）
    local nexus_pids=$(pgrep -f "^nexus-cli" 2>/dev/null)
    log "🔍 nexus-cli进程检查（pgrep）: $nexus_pids"
    
    if [ -n "$nexus_pids" ]; then
        for pid in $nexus_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                local process_info=$(ps -p "$pid" -o pid,ppid,cmd --no-headers 2>/dev/null)
                log "✅ 发现真正的nexus-cli进程: PID=$pid, 信息: $process_info"
                return 0
            fi
        done
    fi
    
    # 方法2: 检查具体的nexus-cli start命令（排除Screen相关）
    local pure_nexus_pids=$(ps aux | grep "nexus-cli start --node-id" | grep -v "SCREEN" | grep -v " -c " | grep -v grep 2>/dev/null)
    log "🔍 纯nexus-cli进程检查: $pure_nexus_pids"
    
    if [ -n "$pure_nexus_pids" ]; then
        local pure_pid=$(echo "$pure_nexus_pids" | awk '{print $2}' | head -1)
        if [ -n "$pure_pid" ] && kill -0 "$pure_pid" 2>/dev/null; then
            local process_info=$(ps -p "$pure_pid" -o pid,ppid,cmd --no-headers 2>/dev/null)
            log "✅ 发现纯nexus-cli进程: PID=$pure_pid, 信息: $process_info"
            return 0
        fi
    fi
    
    # 方法3: 检查进程树中的nexus相关进程
    if check_screen_session; then
        local session_pid=$(screen -list | grep "$SCREEN_SESSION" | awk '{print $1}' | sed 's/\.nexus//')
        if [ -n "$session_pid" ]; then
            # 查找Screen会话的所有子进程
            local child_pids=$(pgrep -P "$session_pid" 2>/dev/null)
            log "🔍 Screen会话子进程: $child_pids"
            
            for child_pid in $child_pids; do
                # 检查子进程是否是nexus-cli
                local child_cmd=$(ps -p "$child_pid" -o cmd --no-headers 2>/dev/null)
                if [[ "$child_cmd" == *"nexus-cli"* ]] && [[ "$child_cmd" != *" -c "* ]]; then
                    log "✅ 在Screen会话中发现nexus-cli进程: PID=$child_pid, CMD: $child_cmd"
                    return 0
                fi
                
                # 递归检查孙进程
                local grandchild_pids=$(pgrep -P "$child_pid" 2>/dev/null)
                for grandchild_pid in $grandchild_pids; do
                    local grandchild_cmd=$(ps -p "$grandchild_pid" -o cmd --no-headers 2>/dev/null)
                    if [[ "$grandchild_cmd" == *"nexus-cli"* ]] && [[ "$grandchild_cmd" != *" -c "* ]]; then
                        log "✅ 在Screen会话的子进程中发现nexus-cli: PID=$grandchild_pid, CMD: $grandchild_cmd"
                        return 0
                    fi
                done
            done
        fi
    fi
    
    log "❌ 未找到运行中的真正nexus-cli进程"
    log "💡 提示：可能只有Screen管理进程存在，但nexus-cli本身未正常启动"
    return 1
}

# 监控模式
monitor_mode() {
    log "📡 进入监控模式，开始持续监控进程状态..."
    
    while true; do
        current_time=$(date +%s)
        
        # 显示状态
        show_status
        
        # 检查进程状态
        if check_process; then
            pids=$(pgrep -f "$PROCESS_NAME" 2>/dev/null)
            if [ -z "$pids" ]; then
                pids=$(pgrep "$PROCESS_NAME" 2>/dev/null)
            fi
            log "✅ 进程运行正常 (PID: $pids)"
        else
            log "❌ 进程已停止，进入重启流程"
            start_nexus
            return
        fi
        
        log "⏰ 等待 ${CHECK_INTERVAL} 秒后进行下次检查..."
        sleep $CHECK_INTERVAL
    done
}

# 启动流程
start_nexus() {
    log "🚀 开始启动流程..."
    
    # 检查依赖
    check_screen
    check_nexus_cli
    
    # 执行启动流程
    if ! create_screen_and_start_nexus; then
        log "❌ 启动流程失败"
        if [ $RESTART_COUNT -lt $MAX_RESTARTS ]; then
            RESTART_COUNT=$((RESTART_COUNT + 1))
            log "🔄 尝试重启 (${RESTART_COUNT}/${MAX_RESTARTS})"
            sleep 5
            start_nexus
        else
            log "⚠️  已达到最大重启次数，停止自动重启"
            log "请手动检查问题并重启"
            exit 1
        fi
    fi
    
    log "✅ 启动流程完成，进入监控模式"
    monitor_mode
}

# 检查screen会话是否存在
check_screen_session() {
    if screen -list | grep -q "$SCREEN_SESSION"; then
        return 0
    else
        return 1
    fi
}

# 获取screen会话详细信息
get_screen_session_info() {
    if check_screen_session; then
        local session_info=$(screen -list | grep "$SCREEN_SESSION")
        log "📺 Screen会话信息: $session_info"
        
        # 尝试获取会话中的进程信息
        local session_pid=$(screen -list | grep "$SCREEN_SESSION" | awk '{print $1}' | sed 's/\.nexus//')
        if [ -n "$session_pid" ]; then
            log "📺 Screen会话PID: $session_pid"
            # 获取会话中运行的进程
            local child_pids=$(pgrep -P "$session_pid" 2>/dev/null)
            if [ -n "$child_pids" ]; then
                log "📺 Screen会话子进程: $child_pids"
            fi
        fi
    else
        log "📺 Screen会话不存在"
    fi
}

# 第一步：创建screen会话并在其中启动nexus
create_screen_and_start_nexus() {
    log "第一步：创建Screen会话 '$SCREEN_SESSION'"
    
    # 生成启动命令（包含动态读取的 Node ID）
    get_start_command
    
    # 如果会话已存在，先删除
    if check_screen_session; then
        log "发现已存在的会话，正在清理..."
        screen -S "$SCREEN_SESSION" -X quit
        sleep 2
    fi
    
    # 检测用户的默认shell
    local user_shell="$SHELL"
    if [ -z "$user_shell" ]; then
        user_shell="/bin/bash"
    fi
    log "使用shell: $user_shell"
    
    # 检查 nexus-cli 的完整路径
    local nexus_path=$(which nexus-cli 2>/dev/null)
    if [ -z "$nexus_path" ]; then
        log "❌ 无法找到 nexus-cli 的完整路径"
        log "💡 尝试常见路径..."
        
        # 尝试更多可能的路径，包括 Nexus 官方安装路径
        local possible_paths=(
            "$HOME/.nexus/nexus-cli"
            "$HOME/.nexus/bin/nexus-cli"
            "/usr/local/bin/nexus-cli"
            "$HOME/bin/nexus-cli"
            "$HOME/.local/bin/nexus-cli"
            # Nexus 官方安装路径
            "$HOME/.nexus-cli/nexus-cli"
            "$HOME/.nexus-network/nexus-cli"
            # 检查是否安装为 nexus-network
            "$HOME/.nexus/nexus-network"
            "$HOME/nexus-network"
            "/usr/local/bin/nexus-network"
        )
        
        for path in "${possible_paths[@]}"; do
            if [ -x "$path" ]; then
                nexus_path="$path"
                log "✅ 找到 nexus-cli: $nexus_path"
                break
            fi
        done
        
        # 如果还是找不到，尝试手动搜索
        if [ -z "$nexus_path" ]; then
            log "🔍 在用户目录下搜索 nexus 相关文件..."
            local found_files=$(find "$HOME" -name "*nexus*" -type f -executable 2>/dev/null | head -5)
            if [ -n "$found_files" ]; then
                log "📁 找到以下可能的文件:"
                echo "$found_files" | while read -r file; do
                    log "   $file"
                done
                # 选择第一个可能的文件
                nexus_path=$(echo "$found_files" | head -1)
                log "🎯 尝试使用: $nexus_path"
            fi
        fi
        
        if [ -z "$nexus_path" ]; then
            log "❌ 仍无法找到 nexus-cli，请检查安装"
            log "💡 建议步骤："
            log "   1. 运行: source ~/.zshrc"
            log "   2. 检查: nexus-cli --version"
            log "   3. 或重新安装: curl https://cli.nexus.xyz/ | sh"
            return 1
        fi
    else
        log "✅ nexus-cli 路径: $nexus_path"
    fi
    
    # 构建完整的启动命令
    local full_start_cmd="$nexus_path start --node-id $NODE_ID"
    log "🚀 完整启动命令: $full_start_cmd"
    
    # 创建启动脚本，包含环境变量和错误处理
    local startup_script="
# 加载 zsh 环境配置
if [ -f ~/.zshrc ]; then
    source ~/.zshrc
fi

# 设置环境变量
export PATH=\$PATH:$HOME/.nexus:/usr/local/bin:$HOME/bin:$HOME/.local/bin
cd $HOME
echo '[INFO] 开始执行 nexus-cli 启动命令...'
echo '[INFO] 当前目录: '\$(pwd)
echo '[INFO] PATH: '\$PATH
echo '[INFO] 执行命令: $full_start_cmd'

# 检查 nexus-cli 是否可用
if command -v nexus-cli >/dev/null 2>&1; then
    echo '[INFO] nexus-cli 命令可用'
    echo '[INFO] nexus-cli 版本: '\$(nexus-cli --version 2>/dev/null || echo 'unknown')
    $full_start_cmd
else
    echo '[ERROR] nexus-cli 命令不可用，尝试使用完整路径'
    if [ -x '$nexus_path' ]; then
        echo '[INFO] 使用完整路径启动: $nexus_path'
        $full_start_cmd
    else
        echo '[ERROR] nexus-cli 不存在或不可执行: $nexus_path'
        echo '[ERROR] 请检查 nexus-cli 是否正确安装'
        echo '[HELP] 建议执行: source ~/.zshrc'
        echo '[HELP] 或重新安装: curl https://cli.nexus.xyz/ | sh'
    fi
fi

echo '[INFO] nexus-cli 执行完成或退出'
# 保持会话打开
exec $user_shell
"
    
    # 创建新的screen会话，使用用户的默认shell
    log "创建新会话并执行启动命令..."
    screen -dmS "$SCREEN_SESSION" "$user_shell" -c "$startup_script"
    
    # 等待一下让screen会话创建完成
    sleep 2
    
    # 检查screen会话状态
    get_screen_session_info
    
    # 等待进程启动
    log "等待进程启动..."
    sleep 60
    
    # 检查进程是否启动成功
    if check_process; then
        pids=$(pgrep -f "$PROCESS_NAME")
        log "✅ 第二步完成：nexus-network进程在Screen会话中启动成功 (PID: $pids)"
        return 0
    else
        log "❌ 第二步失败：nexus-network进程启动失败"
        log "💡 提示：进程可能需要更长时间启动，请检查screen会话状态"
        log "💡 提示：可以使用 'screen -r nexus' 查看会话状态"
        return 1
    fi
}

# 停止nexus进程
stop_nexus() {
    log "停止Nexus进程..."
    
    # 查找并终止nexus进程
    pids=$(pgrep -f "$PROCESS_NAME")
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9
        log "已终止进程: $pids"
    else
        log "未找到运行中的进程"
    fi
    
    # 等待进程完全停止
    sleep 2
}

# 清除nexus会话并重启
clear_session_and_restart() {
    log "🧹 清除nexus会话并重启..."
    
    # 停止进程
    stop_nexus
    
    # 清理screen会话
    if check_screen_session; then
        log "清理Screen会话: $SCREEN_SESSION"
        screen -S "$SCREEN_SESSION" -X quit
        sleep 2
    fi
    
    # 重新执行启动流程
    log "重新执行启动流程..."
    create_screen_and_start_nexus
}

# 重启nexus进程
restart_nexus() {
    log "🔄 重启Nexus进程..."
    
    # 停止进程
    stop_nexus
    
    # 清理screen会话
    if check_screen_session; then
        log "清理Screen会话: $SCREEN_SESSION"
        screen -S "$SCREEN_SESSION" -X quit
        sleep 2
    fi
    
    # 重新执行启动流程
    log "重新执行启动流程..."
    create_screen_and_start_nexus
}

# 显示当前状态
show_status() {
    log "=== 当前状态 ==="
    
    # 检查nexus进程
    if check_process; then
        log "✅ nexus进程运行中"
        
        # 显示真正的nexus-cli进程信息
        local pure_nexus_pids=$(ps aux | grep "nexus-cli start --node-id" | grep -v "SCREEN" | grep -v " -c " | grep -v grep 2>/dev/null)
        if [ -n "$pure_nexus_pids" ]; then
            log "📊 真正的nexus-cli进程信息:"
            echo "$pure_nexus_pids" | while read -r line; do
                local pid=$(echo "$line" | awk '{print $2}')
                local cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
                local cpu=$(echo "$line" | awk '{print $3}')
                local mem=$(echo "$line" | awk '{print $4}')
                log "   PID $pid: CPU=${cpu}%, MEM=${mem}%, CMD: $cmd"
            done
        fi
        
        # 使用pgrep查找真正的nexus-cli进程
        local nexus_pids=$(pgrep -f "^nexus-cli" 2>/dev/null)
        if [ -n "$nexus_pids" ]; then
            log "📊 pgrep找到的nexus-cli进程:"
            for pid in $nexus_pids; do
                local process_info=$(ps -p "$pid" -o pid,ppid,%cpu,%mem,cmd --no-headers 2>/dev/null)
                if [ -n "$process_info" ]; then
                    log "   $process_info"
                fi
            done
        fi
        
        # 显示Screen管理进程（仅作参考）
        local screen_manager_pids=$(ps aux | grep "SCREEN -dmS nexus" | grep -v grep 2>/dev/null)
        if [ -n "$screen_manager_pids" ]; then
            log "🔧 Screen管理进程（仅作参考）:"
            echo "$screen_manager_pids" | while read -r line; do
                local pid=$(echo "$line" | awk '{print $2}')
                log "   PID $pid: SCREEN -dmS nexus"
            done
        fi
    else
        log "❌ nexus进程未运行"
        log "💡 提示：检查Screen会话是否正常启动了nexus-cli"
    fi
    
    # 检查screen会话
    if check_screen_session; then
        log "✅ Screen会话存在: $SCREEN_SESSION"
        get_screen_session_info
    else
        log "❌ Screen会话不存在: $SCREEN_SESSION"
    fi
    
    log "================="
}

# 主监控循环
run_monitor() {
    log "🚀 开始监控Nexus节点..."
    log "进程名称: $PROCESS_NAME"
    log "Screen会话: $SCREEN_SESSION"
    
    # 动态生成启动命令并显示
    get_start_command
    log "监控间隔: ${CHECK_INTERVAL}秒"
    
    # 检查依赖
    check_screen
    
    # 第一步：检查当前状态
    log "🔍 检查当前Nexus状态..."
    show_status
    
    # 第二步：如果nexus未运行，则启动
    if ! check_process; then
        log "❌ Nexus进程未运行，开始启动流程..."
        if ! create_screen_and_start_nexus; then
            log "❌ 启动流程失败，退出监控"
            exit 1
        fi
        log "✅ 启动流程完成"
    else
        log "✅ Nexus进程已在运行，无需启动"
    fi
    
    log "🚀 开始监控循环..."
    restart_count=0
    
    # 第三步：开始监控循环
    while true; do
        current_time=$(date +%s)
        
        # 显示当前状态
        show_status
        
        # 检查nexus进程状态
        if check_process; then
            log "✅ Nexus进程运行正常，继续监控..."
        else
            log "❌ Nexus进程未运行，需要重启..."
            
            if [ $restart_count -lt $MAX_RESTARTS ]; then
                restart_count=$((restart_count + 1))
                log "🔄 尝试重启 (${restart_count}/${MAX_RESTARTS})"
                clear_session_and_restart
            else
                log "⚠️ 已达到最大重启次数 (${MAX_RESTARTS})，停止自动重启"
                log "请手动检查问题并重启"
                break
            fi
        fi
        
        log "⏰ 等待 ${CHECK_INTERVAL} 秒后进行下次检查..."
        sleep $CHECK_INTERVAL
    done
}

# 处理信号
trap 'log "收到停止信号，正在退出..."; exit 0' SIGINT SIGTERM

# 启动监控
run_monitor 