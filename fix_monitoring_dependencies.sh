#!/bin/bash

echo "🔧 修复RL-Swarm监控系统依赖..."

# 检查当前位置
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 请在rl-swarm项目根目录运行此脚本"
    exit 1
fi

echo "📦 重新同步项目依赖..."

# 方法1: 使用uv同步
if command -v uv &> /dev/null; then
    echo "🚀 使用uv重新安装依赖..."
    uv sync --no-dev
    
    # 检查Flask是否安装成功
    if uv run python -c "import flask; print('Flask版本:', flask.__version__)" 2>/dev/null; then
        echo "✅ Flask安装成功!"
    else
        echo "⚠️ uv sync失败，尝试手动安装..."
        uv add flask flask-socketio psutil requests yagmail plotly
    fi
else
    echo "📦 使用pip安装监控依赖..."
    pip install flask flask-socketio psutil requests yagmail plotly
fi

echo ""
echo "🧪 测试监控系统..."

# 测试导入
if python -c "
import flask
import flask_socketio  
import psutil
import requests
import plotly
print('✅ 所有监控依赖导入成功!')
" 2>/dev/null; then
    echo "🎉 监控系统依赖修复完成!"
    echo ""
    echo "现在可以运行监控系统了:"
    echo "  cd ops"
    echo "  python monitoring/real_time_monitor.py"
    echo "  或者运行: ./manage.sh"
else
    echo "❌ 依赖安装仍有问题，请手动检查"
    echo ""
    echo "手动安装命令:"
    echo "  pip install flask flask-socketio psutil requests yagmail plotly"
fi 