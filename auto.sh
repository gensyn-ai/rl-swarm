#!/bin/bash
CONTAINER_NAME="swarm-cpu"
CHECK_INTERVAL=180  # 检查间隔（秒）
LOG_FILE="swarm_launcher.log"  # 要监控的日志文件
STALE_LOG_THRESHOLD=900  # 日志超时阈值（秒）15分钟=900秒

# 检测操作系统类型，确定stat命令的参数
if [[ "$(uname)" == "Darwin" ]]; then
    # macOS/BSD系统
    STAT_CMD="stat -f %m"
else
    # Linux系统
    STAT_CMD="stat -c %Y"
fi

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 开始监控容器: $CONTAINER_NAME，每 $CHECK_INTERVAL 秒检查一次"
echo "[$(date +'%Y-%m-%d %H:%M:%S')] 同时监控日志文件: $LOG_FILE，超过 $STALE_LOG_THRESHOLD 秒无更新将重启容器"

while true; do
    current_time=$(date +%s)  # 当前时间戳（秒）
    restart_needed=0
    
    # 检查容器是否存在
    if ! docker inspect "$CONTAINER_NAME" &> /dev/null; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] 错误: 容器 $CONTAINER_NAME 不存在"
        sleep $CHECK_INTERVAL
        continue
    fi

    # 检查容器是否在运行
    if ! docker ps --filter "name=^/${CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] 容器 $CONTAINER_NAME 已停止，需要启动..."
        restart_needed=1
    else
        # 容器正在运行，检查日志文件
        if [ -f "$LOG_FILE" ]; then
            # 获取日志文件最后修改时间戳（兼容不同系统）
            log_mtime=$($STAT_CMD "$LOG_FILE")
            # 计算与当前时间的差值
            time_diff=$((current_time - log_mtime))
            
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] 容器 $CONTAINER_NAME 运行正常，日志最后更新于 $time_diff 秒前"
            
            # 检查日志是否超过阈值未更新
            if [ $time_diff -gt $STALE_LOG_THRESHOLD ]; then
                echo "[$(date +'%Y-%m-%d %H:%M:%S')] 警告: 日志文件 $LOG_FILE 已超过 $STALE_LOG_THRESHOLD 秒未更新"
                restart_needed=1
            fi
        else
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] 警告: 日志文件 $LOG_FILE 不存在"
            # 可以根据需要决定是否在此情况下重启容器
            # restart_needed=1
        fi
    fi
    
    # 需要重启时执行重启操作
    if [ $restart_needed -eq 1 ]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] 正在重启容器 $CONTAINER_NAME..."
        
        # 先停止容器（防止容器处于异常运行状态）
        if docker stop "$CONTAINER_NAME" &> /dev/null; then
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] 容器 $CONTAINER_NAME 已停止"
        fi
        
        # 启动容器
        if docker start "$CONTAINER_NAME"; then
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] 容器 $CONTAINER_NAME 启动成功"
        else
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] 错误: 容器 $CONTAINER_NAME 启动失败"
        fi
    fi
    
    sleep $CHECK_INTERVAL
done
