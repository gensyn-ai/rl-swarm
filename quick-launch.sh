#!/bin/bash
# RL Swarm 快速启动脚本 - 直接启动4个窗口

# 使用 HOME 环境变量自动适配用户
PROJECT_DIR="$HOME/rl-swarm"
cd "$PROJECT_DIR" || exit 1

echo "🚀 快速启动 RL Swarm 工作环境..."

# 2x2 布局
window_width=640
window_height=360

# 窗口1: Gensyn 训练
osascript -e "
tell application \"Terminal\"
    do script \"cd $PROJECT_DIR && echo '🤖 Gensyn 训练会话' && screen -r gensyn 2>/dev/null || screen -S gensyn\"
    set bounds of front window to {0, 0, $window_width, $window_height}
    set custom title of front window to \"🤖 Gensyn Training\"
end tell"

sleep 1

# 窗口2: Gensyn 监控
osascript -e "
tell application \"Terminal\"
    do script \"cd $PROJECT_DIR && echo '📊 Gensyn 监控会话' && ./auto-run.sh\"
    set bounds of front window to {$window_width, 0, $((window_width*2)), $window_height}
    set custom title of front window to \"📊 Gensyn Monitor\"
end tell"

sleep 1

# 窗口3: Nexus 运行
osascript -e "
tell application \"Terminal\"
    do script \"cd $PROJECT_DIR && echo '🌐 Nexus 运行会话' && screen -r nexus 2>/dev/null || screen -S nexus\"
    set bounds of front window to {0, $window_height, $window_width, $((window_height*2))}
    set custom title of front window to \"🌐 Nexus Node\"
end tell"

sleep 1

# 窗口4: Nexus 监控
osascript -e "
tell application \"Terminal\"
    do script \"cd $PROJECT_DIR && echo '📈 Nexus 监控会话' && ./auto-nexus.sh\"
    set bounds of front window to {$window_width, $window_height, $((window_width*2)), $((window_height*2))}
    set custom title of front window to \"📈 Nexus Monitor\"
end tell"

echo "✅ RL Swarm 工作环境启动完成！"