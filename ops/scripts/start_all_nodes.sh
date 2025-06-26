#!/bin/bash

# Multi-Node Startup Script for Mac Mini M4
# 支持同时运行 RL Swarm, Nexus, Ritual, Worldcoin

set -euo pipefail

GREEN="\033[32m"
BLUE="\033[34m"
RED="\033[31m"
YELLOW="\033[33m"
RESET="\033[0m"

echo_green() { echo -e "$GREEN$1$RESET"; }
echo_blue() { echo -e "$BLUE$1$RESET"; }
echo_red() { echo -e "$RED$1$RESET"; }
echo_yellow() { echo -e "$YELLOW$1$RESET"; }

# 项目路径配置
RL_SWARM_PATH="$HOME/rl-swarm"
NEXUS_PATH="$HOME/nexus-node"
RITUAL_PATH="$HOME/ritual-node" 
WORLDCOIN_PATH="$HOME/worldcoin-node"

# 日志目录
LOG_DIR="$HOME/multi-node-logs"
mkdir -p "$LOG_DIR"

# 检查系统资源
check_resources() {
    echo_blue ">> 检查系统资源..."
    
    # 检查内存
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    echo "总内存: ${TOTAL_MEM}GB"
    
    if [ "$TOTAL_MEM" -lt 16 ]; then
        echo_red "警告: 内存小于16GB，可能影响性能"
    fi
    
    # 检查可用端口
    for PORT in 3000 8080 8081 8082 38331; do
        if lsof -i :$PORT >/dev/null 2>&1; then
            echo_yellow "警告: 端口 $PORT 已被占用"
        fi
    done
}

# 启动 RL Swarm (Gensyn)
start_rl_swarm() {
    echo_green ">> 启动 RL Swarm (Gensyn)..."
    
    if [ ! -d "$RL_SWARM_PATH" ]; then
        echo_red "错误: RL Swarm 路径不存在: $RL_SWARM_PATH"
        return 1
    fi
    
    cd "$RL_SWARM_PATH"
    nohup ./run_rl_swarm_mac.sh > "$LOG_DIR/rl-swarm.log" 2>&1 &
    RL_SWARM_PID=$!
    echo "RL Swarm PID: $RL_SWARM_PID"
    echo $RL_SWARM_PID > "$LOG_DIR/rl-swarm.pid"
}

# 启动 Nexus Network
start_nexus() {
    echo_green ">> 启动 Nexus Network..."
    
    if ! command -v nexus &> /dev/null; then
        echo_red "错误: Nexus CLI 未安装"
        return 1
    fi
    
    cd "$NEXUS_PATH"
    nohup nexus node start --mode prover --port 8080 > "$LOG_DIR/nexus.log" 2>&1 &
    NEXUS_PID=$!
    echo "Nexus PID: $NEXUS_PID"
    echo $NEXUS_PID > "$LOG_DIR/nexus.pid"
}

# 启动 Ritual AI
start_ritual() {
    echo_green ">> 启动 Ritual AI..."
    
    if ! command -v docker &> /dev/null; then
        echo_red "错误: Docker 未安装"
        return 1
    fi
    
    # 检查 Docker 是否运行
    if ! docker info >/dev/null 2>&1; then
        echo_yellow "启动 Docker..."
        open -a Docker
        sleep 10
    fi
    
    # 启动 Ritual 容器
    docker run -d \
        --name ritual-node-$(date +%s) \
        --restart unless-stopped \
        -p 8081:8081 \
        -v "$RITUAL_PATH/config.yaml:/app/config.yaml" \
        -v "$RITUAL_PATH/models:/tmp/ritual-models" \
        ritualnetwork/ritual-node:latest > "$LOG_DIR/ritual.log" 2>&1
    
    RITUAL_CONTAINER=$(docker ps -q -f name=ritual-node)
    echo "Ritual Container ID: $RITUAL_CONTAINER"
    echo $RITUAL_CONTAINER > "$LOG_DIR/ritual.pid"
}

# 启动 Worldcoin
start_worldcoin() {
    echo_green ">> 启动 Worldcoin..."
    
    if ! command -v worldcoin-node &> /dev/null; then
        echo_red "错误: Worldcoin node 未安装"
        return 1
    fi
    
    cd "$WORLDCOIN_PATH"
    nohup worldcoin-node start --port 8082 > "$LOG_DIR/worldcoin.log" 2>&1 &
    WORLDCOIN_PID=$!
    echo "Worldcoin PID: $WORLDCOIN_PID"
    echo $WORLDCOIN_PID > "$LOG_DIR/worldcoin.pid"
}

# 检查服务状态
check_status() {
    echo_blue ">> 检查服务状态..."
    
    # 检查进程
    for service in rl-swarm nexus worldcoin; do
        if [ -f "$LOG_DIR/${service}.pid" ]; then
            PID=$(cat "$LOG_DIR/${service}.pid")
            if ps -p $PID > /dev/null; then
                echo_green "✅ $service 运行中 (PID: $PID)"
            else
                echo_red "❌ $service 已停止"
            fi
        fi
    done
    
    # 检查 Ritual 容器
    if [ -f "$LOG_DIR/ritual.pid" ]; then
        CONTAINER_ID=$(cat "$LOG_DIR/ritual.pid")
        if docker ps -q --no-trunc | grep -q $CONTAINER_ID; then
            echo_green "✅ Ritual AI 运行中 (Container: $CONTAINER_ID)"
        else
            echo_red "❌ Ritual AI 已停止"
        fi
    fi
    
    # 检查端口
    echo_blue "\n>> 检查端口状态..."
    for PORT in 3000 8080 8081 8082 38331; do
        if lsof -i :$PORT >/dev/null 2>&1; then
            echo_green "✅ 端口 $PORT 正在使用"
        else
            echo_yellow "⚠️  端口 $PORT 未使用"
        fi
    done
}

# 停止所有服务
stop_all() {
    echo_red ">> 停止所有服务..."
    
    # 停止进程
    for service in rl-swarm nexus worldcoin; do
        if [ -f "$LOG_DIR/${service}.pid" ]; then
            PID=$(cat "$LOG_DIR/${service}.pid")
            if ps -p $PID > /dev/null; then
                kill $PID
                echo "已停止 $service (PID: $PID)"
            fi
            rm -f "$LOG_DIR/${service}.pid"
        fi
    done
    
    # 停止 Ritual 容器
    docker stop $(docker ps -q -f name=ritual-node) 2>/dev/null || true
    docker rm $(docker ps -aq -f name=ritual-node) 2>/dev/null || true
    rm -f "$LOG_DIR/ritual.pid"
    
    echo_green "所有服务已停止"
}

# 显示日志
show_logs() {
    echo_blue ">> 实时日志 (Ctrl+C 退出)..."
    tail -f "$LOG_DIR"/*.log
}

# 资源监控
monitor_resources() {
    echo_blue ">> 系统资源监控..."
    
    while true; do
        clear
        echo "=== Multi-Node 资源监控 ==="
        echo "时间: $(date)"
        echo
        
        # CPU 使用率
        CPU_USAGE=$(top -l 1 -s 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
        echo "CPU 使用率: ${CPU_USAGE}%"
        
        # 内存使用率  
        MEM_INFO=$(vm_stat | grep -E "(free|active|inactive|speculative|wired)" | awk '{print $3}' | sed 's/\.//')
        FREE=$(echo $MEM_INFO | awk '{print $1}')
        ACTIVE=$(echo $MEM_INFO | awk '{print $2}')
        INACTIVE=$(echo $MEM_INFO | awk '{print $3}')
        WIRED=$(echo $MEM_INFO | awk '{print $5}')
        
        TOTAL_PAGES=$((FREE + ACTIVE + INACTIVE + WIRED))
        USED_PAGES=$((ACTIVE + INACTIVE + WIRED))
        MEM_USAGE=$((USED_PAGES * 100 / TOTAL_PAGES))
        
        echo "内存使用率: ${MEM_USAGE}%"
        
        # 网络连接
        CONNECTIONS=$(netstat -an | grep ESTABLISHED | wc -l)
        echo "网络连接数: $CONNECTIONS"
        
        echo
        check_status
        
        sleep 5
    done
}

# 主菜单
show_menu() {
    echo_blue "=== Mac Mini M4 多节点管理器 ==="
    echo "1. 检查系统资源"
    echo "2. 启动所有服务"
    echo "3. 启动单个服务"
    echo "4. 检查服务状态" 
    echo "5. 查看日志"
    echo "6. 资源监控"
    echo "7. 停止所有服务"
    echo "8. 退出"
    echo
}

# 主程序
main() {
    while true; do
        show_menu
        read -p "请选择操作 [1-8]: " choice
        
        case $choice in
            1)
                check_resources
                ;;
            2)
                check_resources
                start_rl_swarm
                sleep 5
                start_nexus  
                sleep 3
                start_ritual
                sleep 3
                start_worldcoin
                echo_green "\n>> 所有服务启动完成！"
                check_status
                ;;
            3)
                echo "选择要启动的服务:"
                echo "1. RL Swarm"
                echo "2. Nexus"  
                echo "3. Ritual AI"
                echo "4. Worldcoin"
                read -p "请选择 [1-4]: " svc_choice
                
                case $svc_choice in
                    1) start_rl_swarm ;;
                    2) start_nexus ;;
                    3) start_ritual ;;
                    4) start_worldcoin ;;
                esac
                ;;
            4)
                check_status
                ;;
            5)
                show_logs
                ;;
            6)
                monitor_resources
                ;;
            7)
                stop_all
                ;;
            8)
                echo_green "再见！"
                exit 0
                ;;
            *)
                echo_red "无效选择，请重试"
                ;;
        esac
        
        echo
        read -p "按 Enter 继续..."
        clear
    done
}

# 执行主程序
main "$@" 