#!/bin/bash
LOG_FILE="auto_monitor.log"
RL_LOG_FILE="logs/swarm_launcher.log"
SESSION_NAME="gensyn"
MAIN_CMD="./run_rl_swarm.sh"   # 必须与auto-screen.sh一致
RESTART_COUNT=0
MONITOR_INTERVAL=300  # 监控间隔300秒

# 自动检查和创建screen会话
setup_screen_session() {
    echo "[🔄 设置] 检查并设置screen会话..."
    
    # 检查是否存在名为gensyn的screen会话（包括死会话）
    local session_exists=false
    local session_status=""
    
    # 获取会话详细信息
    if screen -list | grep -q "$SESSION_NAME"; then
        session_exists=true
        session_status=$(screen -list | grep "$SESSION_NAME" | head -1)
        echo "[🔍 设置] 检测到$SESSION_NAME会话: $session_status"
        
        # 尝试多种方式清除会话
        echo "[🗑️ 设置] 正在清除$SESSION_NAME会话..."
        
        # 方法1: 尝试正常退出
        if screen -S "$SESSION_NAME" -X quit >/dev/null 2>&1; then
            echo "[✅ 设置] 正常退出会话成功"
        else
            echo "[⚠️ 设置] 正常退出失败，尝试强制清除..."
            
            # 方法2: 尝试kill会话
            if screen -S "$SESSION_NAME" -X kill >/dev/null 2>&1; then
                echo "[✅ 设置] 强制kill会话成功"
            else
                echo "[⚠️ 设置] 强制kill失败，尝试清理socket文件..."
                
                # 方法3: 清理socket文件（处理死会话）
                local socket_dir="$HOME/.screen"
                local socket_file=""
                
                # 查找对应的socket文件
                if [ -d "$socket_dir" ]; then
                    socket_file=$(find "$socket_dir" -name "*$SESSION_NAME*" 2>/dev/null | head -1)
                    if [ -n "$socket_file" ]; then
                        echo "[🗑️ 设置] 找到socket文件: $socket_file"
                        if rm -f "$socket_file" 2>/dev/null; then
                            echo "[✅ 设置] 成功删除socket文件"
                        else
                            echo "[❌ 设置] 删除socket文件失败"
                        fi
                    fi
                fi
            fi
        fi
        
        # 等待一下确保会话完全清除
        sleep 2
        
        # 再次检查会话是否还存在
        if screen -list | grep -q "$SESSION_NAME"; then
            echo "[⚠️ 设置] 会话仍存在，尝试最后手段..."
            # 最后手段：使用pkill强制结束所有相关进程
            pkill -f "screen.*$SESSION_NAME" 2>/dev/null
            sleep 1
        fi
    else
        echo "[✅ 设置] 未检测到$SESSION_NAME会话"
    fi
    
    # 确保没有残留的会话
    if screen -list | grep -q "$SESSION_NAME"; then
        echo "[❌ 设置] 无法完全清除$SESSION_NAME会话，退出脚本"
        exit 1
    fi
    
    # 创建新的screen会话
    echo "[🆕 设置] 创建新的$SESSION_NAME会话..."
    screen -dmS "$SESSION_NAME"
    sleep 2
    
    # 验证会话是否创建成功
    if screen -list | grep -q "$SESSION_NAME"; then
        echo "[✅ 设置] 成功创建$SESSION_NAME会话"
        echo "[📱 设置] 可以使用 'screen -r $SESSION_NAME' 连接到会话"
        
        # 初始化会话环境
        echo "[🔧 设置] 初始化会话环境..."
        
        # 立即启动程序
        echo "[🚀 设置] 启动RL Swarm程序..."
        STARTUP_CMD='if [ -z "$VIRTUAL_ENV" ]; then source venv/bin/activate; fi; export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 && export PYTORCH_ENABLE_MPS_FALLBACK=1 && MODEL_NAME="Gensyn/Qwen2.5-0.5B-Instruct"; (echo "n"; echo "$MODEL_NAME") | ./run_rl_swarm.sh\n'
        screen -S "$SESSION_NAME" -p 0 -X stuff "$STARTUP_CMD"
        sleep 8
        
        screen -S "$SESSION_NAME" -p 0 -X stuff "echo '🚀 程序已启动，等待连接...'\r"
        sleep 1
        
        # 验证会话响应
        if screen -S "$SESSION_NAME" -X select 0 >/dev/null 2>&1; then
            echo "[✅ 设置] screen会话响应正常"
        else
            echo "[⚠️ 设置] screen会话响应异常"
        fi
    else
        echo "[❌ 设置] 创建$SESSION_NAME会话失败，退出脚本"
        exit 1
    fi
    
    echo "[🚀 设置] screen会话设置完成，开始监控..."
}

# 输出项目相关进程信息
show_process_info() {
    echo "=== 项目运行进程信息 ==="
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    swarm_pids=$(pgrep -f "swarm_launcher")
    if [ -n "$swarm_pids" ]; then
        echo "swarm_launcher 进程:"
        for pid in $swarm_pids; do
            echo "  PID: $pid - $(ps -p $pid -o command=)"
        done
    else
        echo "swarm_launcher 进程: 未运行"
    fi
    run_script_pids=$(pgrep -f "run_rl_swarm.sh")
    if [ -n "$run_script_pids" ]; then
        echo "run_rl_swarm.sh 进程:"
        for pid in $run_script_pids; do
            echo "  PID: $pid - $(ps -p $pid -o command=)"
        done
    else
        echo "run_rl_swarm.sh 进程: 未运行"
    fi
    p2pd_pids=$(pgrep -f "p2pd")
    if [ -n "$p2pd_pids" ]; then
        echo "p2pd 进程: $p2pd_pids"
    fi
    node_pids=$(pgrep -f "node")
    if [ -n "$node_pids" ]; then
        echo "node 进程: $node_pids"
    fi
    port_3000_pids=$(lsof -ti:3000 2>/dev/null)
    if [ -n "$port_3000_pids" ]; then
        echo "3000端口占用进程: $port_3000_pids"
    fi
    echo "========================"
}

# 执行重启流程
execute_restart() {
    echo "[🔄 重启] 开始执行重启流程..."
    RESTART_COUNT=$((RESTART_COUNT+1))
    
    # 清理现有进程
    project_dir="$(cd "$(dirname "$0")/.." && pwd)"
    py_pids=$(ps aux | grep python | grep "$project_dir" | awk '{print $2}')
    if [ -n "$py_pids" ]; then
        echo "[🧹 重启] 清理本项目 Python 进程: $py_pids"
        echo "$py_pids" | xargs kill -9
    fi
    
    p2pd_pids=$(pgrep -f "p2pd")
    [ -n "$p2pd_pids" ] && echo "[🧹 重启] 清理 p2pd 进程: $p2pd_pids" && pkill -f "p2pd"
    
    node_pids=$(pgrep -f "node")
    [ -n "$node_pids" ] && echo "[🧹 重启] 清理 node 进程: $node_pids" && pkill -f "node"
    
    port_3000_pids=$(lsof -ti:3000 2>/dev/null)
    if [ -n "$port_3000_pids" ]; then
        echo "[🧹 重启] 清理 3000 端口占用进程: $port_3000_pids"
        echo "$port_3000_pids" | xargs kill -9
    fi
    
    # 清空日志
    > "$RL_LOG_FILE"
    
    # 停止 screen 会话中的当前命令
    screen -S "$SESSION_NAME" -p 0 -X stuff "\003"
    sleep 2
    
    # 发送启动命令到 screen 会话
    echo "[🚀 重启] 向 screen 会话发送启动命令..."
    
    # 分步发送命令，确保每个命令都能执行
    screen -S "$SESSION_NAME" -p 0 -X stuff "cd $(pwd)\r"
    sleep 2
    screen -S "$SESSION_NAME" -p 0 -X stuff "source venv/bin/activate\r"
    sleep 2
    screen -S "$SESSION_NAME" -p 0 -X stuff "export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0\r"
    sleep 1
    screen -S "$SESSION_NAME" -p 0 -X stuff "export PYTORCH_ENABLE_MPS_FALLBACK=1\r"
    sleep 1
    
    # 最简单直接的启动方式
    echo "[🚀 重启] 直接启动RL Swarm..."
    
    # 使用智能重启命令，自动处理虚拟环境和交互问题
    RESTART_CMD='if [ -z "$VIRTUAL_ENV" ]; then source venv/bin/activate; fi; export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 && export PYTORCH_ENABLE_MPS_FALLBACK=1 && MODEL_NAME="Gensyn/Qwen2.5-0.5B-Instruct"; (echo "n"; echo "$MODEL_NAME") | ./run_rl_swarm.sh\n'
    screen -S "$SESSION_NAME" -p 0 -X stuff "$RESTART_CMD"
    sleep 8
    
    echo "[✅ 重启] 启动命令发送完成"
    
    echo "[✅ 重启] 已向'主程序'窗口发送第${RESTART_COUNT}次重启命令，日志已清空，等待主程序恢复..."
    
    # 验证screen会话状态
    echo "[🔍 重启] 验证screen会话状态..."
    if screen -list | grep -q "$SESSION_NAME"; then
        echo "[✅ 重启] screen会话 '$SESSION_NAME' 存在"
        # 检查会话是否可访问
        if screen -S "$SESSION_NAME" -X select 0 >/dev/null 2>&1; then
            echo "[✅ 重启] screen会话可正常访问"
        else
            echo "[⚠️ 重启] screen会话访问异常，可能需要手动检查"
        fi
    else
        echo "[❌ 重启] screen会话 '$SESSION_NAME' 不存在，重新创建..."
        screen -dmS "$SESSION_NAME"
        sleep 2
    fi
    
    sleep 10
}

# 检查是否已连接到 Gensyn Testnet
check_connection() {
    if [ -f "$RL_LOG_FILE" ] && tail -n 200 "$RL_LOG_FILE" | grep -a -q "Connected to Gensyn Testnet"; then
        return 0  # 已连接
    fi
    return 1  # 未连接
}

# 检查主程序是否存在
check_main_process() {
    if pgrep -f "swarm_launcher" > /dev/null 2>&1 || pgrep -f "run_rl_swarm.sh" > /dev/null 2>&1; then
        return 0  # 存在
    fi
    return 1  # 不存在
}

# 检查主程序是否异常
check_anomaly() {
    swarm_count=$(pgrep -f "swarm_launcher" | wc -l | awk '{print $1}')
    if [ -z "$swarm_count" ]; then swarm_count=0; fi
    if [ "$swarm_count" -ne 2 ]; then
        ANOMALY_REASON="swarm_launcher父子进程缺失（当前$swarm_count个，需要2个）"
        return 0
    fi
    if [ -f "$RL_LOG_FILE" ] && tail -n 50 "$RL_LOG_FILE" | grep -a -q "Shutting down trainer\|An error was detected while running rl-swarm\|Killed: 9"; then
        ANOMALY_REASON="日志出现错误信息"
        return 0
    fi
    if [ -f "$RL_LOG_FILE" ]; then
        local rl_log_mtime=$(stat -f %m "$RL_LOG_FILE" 2>/dev/null || stat -c %Y "$RL_LOG_FILE" 2>/dev/null)
        local current_time=$(date +%s)
        local time_diff=$((current_time - rl_log_mtime))
        if [ $time_diff -gt 3600 ]; then
            ANOMALY_REASON="日志1小时未更新"
            return 0
        fi
    fi
    return 1
}

echo "[🚀 监控] 启动Gensyn训练监控脚本..."

# 设置screen会话
setup_screen_session

while true; do
    show_process_info
    # 先检查主程序进程是否存在
    if ! check_main_process; then
        echo "[❌ 监控] 主程序未运行，立即执行重启流程..."
        execute_restart
        continue
    fi

    # 主程序存在，判断是否已连接
    if check_connection; then
        echo "[✅ 监控] 已连接到 Gensyn Testnet，进入常规监控模式。"
        # 检查异常情况
        check_anomaly
        if [ $? -eq 0 ]; then
            # 检查是否因为进程数不是2个导致异常
            swarm_count=$(pgrep -f "swarm_launcher" | wc -l | awk '{print $1}')
            if [ -z "$swarm_count" ]; then swarm_count=0; fi
            if [ "$swarm_count" -ne 2 ]; then
                echo "[⏳ 监控] 检测到swarm_launcher进程数为${swarm_count}，进入120秒宽限期..."
                sleep 120
                # 宽限期后再检测一次
                swarm_count2=$(pgrep -f "swarm_launcher" | wc -l | awk '{print $1}')
                if [ -z "$swarm_count2" ]; then swarm_count2=0; fi
                if [ "$swarm_count2" -ne 2 ]; then
                    echo "[📸️ 监控] 宽限期后进程数仍为${swarm_count2}，执行重启流程..."
                    execute_restart
                    continue
                else
                    echo "[✅ 监控] 宽限期后进程数恢复为2，继续监控。"
                fi
            else
                # 其他异常（如日志报错、日志未更新）直接重启
                echo "[📸️ 监控] 检测到主程序${ANOMALY_REASON}，执行重启流程..."
                execute_restart
                continue
            fi
        else
            echo "[📸️ 监控] 主程序运行正常，无需重启。$(date '+%Y-%m-%d %H:%M:%S')"
        fi
        echo "[⏰ 监控] 等待 ${MONITOR_INTERVAL} 秒后进行下次检查..."
        sleep $MONITOR_INTERVAL
        continue
    else
        echo "[📋 监控] 未检测到连接，进入5分钟等待连接阶段..."
        connection_timeout=300  # 5分钟
        connection_check_interval=10
        connection_elapsed=0
        connected=false
        while [ $connection_elapsed -lt $connection_timeout ]; do
            if check_connection; then
                echo "[✅ 监控] 检测到已连接到 Gensyn Testnet！"
                connected=true
                break
            fi
            echo "[⏳ 监控] 等待连接Gensyn Testnet... 已等待${connection_elapsed}秒"
            sleep $connection_check_interval
            connection_elapsed=$((connection_elapsed+connection_check_interval))
        done
        if ! $connected; then
            echo "[❌ 监控] 5分钟内未检测到连接Gensyn Testnet，执行重启..."
            execute_restart
            continue
        fi
        echo "[🚦 监控] 已连接到Gensyn Testnet，进入常规监控模式，每${MONITOR_INTERVAL}秒检查一次进程..."
    fi
    # 进入下一轮循环
    sleep 5

done

