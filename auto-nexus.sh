#!/bin/bash

# Nexus节点监控脚本 - 清晰流程版本
# 流程：创建screen会话 -> 在会话中启动nexus -> 监控进程
# 新增：每10分钟检查CPU进程状态，异常时清除会话并重启

# ==================== 配置区域 ====================
# 进程名称（用于查找nexus进程）
PROCESS_NAME="nexus-network"

# Screen会话名称
SCREEN_SESSION="nexus"

# 启动命令
START_CMD="nexus-cli start --node-id 35915268"

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


# 检查进程状态
check_process() {
    log "🔍 开始检测进程状态..."
    
    # 方法1: 检查主要的nexus-cli start进程（核心进程）
    local main_nexus_pids=$(ps aux | grep "nexus-cli start" | grep -v grep 2>/dev/null)
    log "🔍 主要nexus-cli进程检查: $main_nexus_pids"
    
    if [ -n "$main_nexus_pids" ]; then
        # 提取PID并验证进程存活
        local main_pid=$(echo "$main_nexus_pids" | awk '{print $2}' | head -1)
        if [ -n "$main_pid" ] && kill -0 "$main_pid" 2>/dev/null; then
            local process_info=$(ps -p "$main_pid" -o pid,ppid,cmd --no-headers 2>/dev/null)
            log "✅ 发现主要nexus-cli进程: PID=$main_pid, 信息: $process_info"
            return 0
        fi
    fi
    
    # 方法2: 检查screen会话中的nexus进程
    local screen_nexus_pids=$(ps aux | grep "bash -c nexus-cli start" | grep -v grep 2>/dev/null)
    log "🔍 Screen中的nexus进程检查: $screen_nexus_pids"
    
    if [ -n "$screen_nexus_pids" ]; then
        local screen_pid=$(echo "$screen_nexus_pids" | awk '{print $2}' | head -1)
        if [ -n "$screen_pid" ] && kill -0 "$screen_pid" 2>/dev/null; then
            log "✅ 发现Screen中的nexus进程: PID=$screen_pid"
            return 0
        fi
    fi
    
    # 方法3: 检查SCREEN管理进程
    local screen_manager_pids=$(ps aux | grep "SCREEN -dmS nexus" | grep -v grep 2>/dev/null)
    log "🔍 Screen管理进程检查: $screen_manager_pids"
    
    if [ -n "$screen_manager_pids" ]; then
        local manager_pid=$(echo "$screen_manager_pids" | awk '{print $2}' | head -1)
        if [ -n "$manager_pid" ] && kill -0 "$manager_pid" 2>/dev/null; then
            log "✅ 发现Screen管理进程: PID=$manager_pid"
            return 0
        fi
    fi
    
    # 方法4: 使用pgrep检查（备用方法）
    local pgrep_pids=$(pgrep -f "nexus-cli start" 2>/dev/null)
    log "🔍 pgrep检查结果: $pgrep_pids"
    
    if [ -n "$pgrep_pids" ]; then
        for pid in $pgrep_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                log "✅ 通过pgrep发现进程: PID=$pid"
                return 0
            fi
        done
    fi
    
    log "❌ 未找到运行中的nexus进程"
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
    
    # 如果会话已存在，先删除
    if check_screen_session; then
        log "发现已存在的会话，正在清理..."
        screen -S "$SCREEN_SESSION" -X quit
        sleep 2
    fi
    
    # 创建新的screen会话，在后台运行nexus-cli
    log "创建新会话并执行启动命令..."
    screen -dmS "$SCREEN_SESSION" bash -c "$START_CMD; exec bash"
    
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
        
        # 显示主要nexus-cli进程信息
        local main_nexus_pids=$(ps aux | grep "nexus-cli start" | grep -v grep 2>/dev/null)
        if [ -n "$main_nexus_pids" ]; then
            log "📊 主要进程信息:"
            echo "$main_nexus_pids" | while read -r line; do
                local pid=$(echo "$line" | awk '{print $2}')
                local cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
                local cpu=$(echo "$line" | awk '{print $3}')
                local mem=$(echo "$line" | awk '{print $4}')
                log "   PID $pid: CPU=${cpu}%, MEM=${mem}%, CMD: $cmd"
            done
        fi
        
        # 显示screen相关进程
        local screen_nexus_pids=$(ps aux | grep "bash -c nexus-cli start" | grep -v grep 2>/dev/null)
        if [ -n "$screen_nexus_pids" ]; then
            log "📺 Screen会话进程:"
            echo "$screen_nexus_pids" | while read -r line; do
                local pid=$(echo "$line" | awk '{print $2}')
                log "   PID $pid: bash -c nexus-cli start"
            done
        fi
        
        # 显示SCREEN管理进程
        local screen_manager_pids=$(ps aux | grep "SCREEN -dmS nexus" | grep -v grep 2>/dev/null)
        if [ -n "$screen_manager_pids" ]; then
            log "🔧 Screen管理进程:"
            echo "$screen_manager_pids" | while read -r line; do
                local pid=$(echo "$line" | awk '{print $2}')
                log "   PID $pid: SCREEN -dmS nexus"
            done
        fi
    else
        log "❌ nexus进程未运行"
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
    log "启动命令: $START_CMD"
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