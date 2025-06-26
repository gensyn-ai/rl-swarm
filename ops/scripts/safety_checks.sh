#!/bin/bash

# RL-Swarm 安全检查模块
# 可被其他启动脚本引用，避免代码重复

# 颜色定义（如果未定义）
GREEN_TEXT="${GREEN_TEXT:-\033[32m}"
BLUE_TEXT="${BLUE_TEXT:-\033[34m}"
YELLOW_TEXT="${YELLOW_TEXT:-\033[33m}"
RED_TEXT="${RED_TEXT:-\033[31m}"
RESET_TEXT="${RESET_TEXT:-\033[0m}"

# 安全检查函数
safety_echo_green() {
    echo -e "$GREEN_TEXT$1$RESET_TEXT"
}

safety_echo_blue() {
    echo -e "$BLUE_TEXT$1$RESET_TEXT"
}

safety_echo_yellow() {
    echo -e "$YELLOW_TEXT$1$RESET_TEXT"
}

safety_echo_red() {
    echo -e "$RED_TEXT$1$RESET_TEXT"
}

# 检查是否有正在运行的训练进程
safety_check_running_processes() {
    safety_echo_blue "🔍 检查是否有正在运行的 RL-Swarm 进程..."
    
    local running_procs=$(ps aux | grep -E "(train_single_gpu|hivemind_grpo)" | grep -v grep | wc -l)
    
    if [ "$running_procs" -gt 0 ]; then
        safety_echo_red "❌ 发现 $running_procs 个正在运行的训练进程："
        ps aux | grep -E "(train_single_gpu|hivemind_grpo)" | grep -v grep
        echo ""
        safety_echo_yellow "⚠️ 请选择操作："
        echo "1) 自动清理并继续启动"
        echo "2) 手动处理后退出"
        echo "3) 强制继续（不推荐）"
        
        read -p "请输入选择 [1/2/3]: " choice
        case $choice in
            1)
                safety_echo_green "🧹 正在清理现有进程..."
                sudo pkill -f "train_single_gpu" || true
                sudo pkill -f "hivemind_grpo" || true
                sudo pkill -f "run_rl_swarm_mac.sh" || true
                sleep 5
                safety_echo_green "✅ 清理完成"
                return 0
                ;;
            2)
                safety_echo_yellow "请手动处理现有进程后重新运行此脚本"
                exit 0
                ;;
            3)
                safety_echo_red "⚠️ 强制继续可能导致资源冲突"
                return 0
                ;;
            *)
                safety_echo_red "无效选择，退出"
                exit 1
                ;;
        esac
    else
        safety_echo_green "✅ 没有发现冲突进程"
        return 0
    fi
}

# 检查系统内存
safety_check_memory_usage() {
    safety_echo_blue "🧠 检查系统内存使用情况..."
    
    local memory_info=$(top -l 1 | grep PhysMem)
    local unused_mem=$(echo $memory_info | awk '{print $6}' | sed 's/M//')
    
    safety_echo_yellow "   $memory_info"
    
    # 转换为数字进行比较（假设unused_mem是MB）
    if [ "${unused_mem%.*}" -lt 2000 ]; then
        safety_echo_red "⚠️ 可用内存不足 2GB，可能影响训练性能"
        safety_echo_yellow "建议释放一些内存后再启动"
        read -p "是否继续启动？[y/N]: " continue_choice
        if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
            safety_echo_yellow "启动已取消"
            exit 0
        fi
    else
        safety_echo_green "✅ 内存充足"
    fi
    return 0
}

# 创建进程锁文件
safety_create_lock_file() {
    local lock_file="/tmp/rl_swarm_training.lock"
    
    if [ -f "$lock_file" ]; then
        local lock_pid=$(cat "$lock_file" 2>/dev/null || echo "")
        if [ -n "$lock_pid" ] && kill -0 "$lock_pid" 2>/dev/null; then
            safety_echo_red "❌ 另一个训练实例正在运行 (PID: $lock_pid)"
            exit 1
        else
            safety_echo_yellow "⚠️ 发现过期的锁文件，正在清理..."
            rm -f "$lock_file"
        fi
    fi
    
    echo $$ > "$lock_file"
    safety_echo_green "🔒 创建进程锁: $lock_file"
    
    # 确保退出时清理锁文件
    trap "rm -f $lock_file" EXIT
    return 0
}

# 启动内存监控
safety_start_memory_monitor() {
    safety_echo_blue "📊 启动内存监控..."
    
    # 创建logs目录
    mkdir -p logs
    
    (
        while true; do
            local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            local memory_info=$(top -l 1 | grep PhysMem)
            local cpu_info=$(top -l 1 | grep "CPU usage")
            
            echo "[$timestamp] Memory: $memory_info" >> logs/system_monitor.log
            echo "[$timestamp] CPU: $cpu_info" >> logs/system_monitor.log
            
            # 检查内存是否过低
            local unused_mem=$(echo $memory_info | awk '{print $6}' | sed 's/M//')
            if [ "${unused_mem%.*}" -lt 500 ]; then
                echo "[$timestamp] ⚠️ 内存不足警告: 可用内存 ${unused_mem}M" >> logs/system_monitor.log
            fi
            
            sleep 30
        done
    ) &
    
    local monitor_pid=$!
    safety_echo_green "✅ 内存监控已启动 (PID: $monitor_pid)"
    
    # 确保退出时停止监控
    trap "kill $monitor_pid 2>/dev/null || true; rm -f /tmp/rl_swarm_training.lock" EXIT
    return 0
}

# 执行完整的安全检查
run_safety_checks() {
    safety_echo_green ">> 🛡️ 开始安全检查..."
    
    # 依次执行各项检查
    safety_check_running_processes
    safety_check_memory_usage
    safety_create_lock_file
    safety_start_memory_monitor
    
    safety_echo_green ">> ✅ 安全检查完成"
    safety_echo_blue ">> 📝 系统监控日志: tail -f logs/system_monitor.log"
    return 0
}

# 如果直接执行此脚本，则运行完整安全检查
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_safety_checks
fi 