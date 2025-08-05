#!/bin/bash

# RL-Swarm 节点可见性诊断脚本
# 用于排查节点为什么在仪表板上不显示

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_green() { echo -e "${GREEN}$1${NC}"; }
echo_yellow() { echo -e "${YELLOW}$1${NC}"; }
echo_red() { echo -e "${RED}$1${NC}"; }
echo_blue() { echo -e "${BLUE}$1${NC}"; }

echo_blue "🔍 RL-Swarm 节点可见性诊断工具"
echo_blue "=================================="

# 1. 检查ORG_ID
echo_yellow "\n📋 1. 检查身份信息..."
if [ -f "modal-login/temp-data/userData.json" ]; then
    ORG_ID=$(awk 'BEGIN { FS = "\"" } !/^[ \t]*[{}]/ { print $(NF - 1); exit }' modal-login/temp-data/userData.json)
    if [ -n "$ORG_ID" ]; then
        echo_green "✅ ORG_ID 已找到: $ORG_ID"
    else
        echo_red "❌ ORG_ID 为空"
        echo "请重新运行登录流程: ./manage.sh"
        exit 1
    fi
else
    echo_red "❌ 用户数据文件不存在"
    echo "请先运行: ./manage.sh 进行登录"
    exit 1
fi

# 2. 检查API密钥状态
echo_yellow "\n🔑 2. 检查API密钥状态..."
if curl -s "http://localhost:3000" > /dev/null 2>&1; then
    API_STATUS=$(curl -s "http://localhost:3000/api/get-api-key-status?orgId=$ORG_ID" 2>/dev/null || echo "error")
    if [ "$API_STATUS" = "activated" ]; then
        echo_green "✅ API密钥已激活"
    elif [ "$API_STATUS" = "pending" ]; then
        echo_yellow "⚠️  API密钥待激活，请检查邮箱"
    else
        echo_red "❌ API密钥状态异常: $API_STATUS"
        echo "请重新运行登录流程"
    fi
else
    echo_red "❌ 本地服务器未运行 (localhost:3000)"
    echo "请先启动服务: ./manage.sh"
fi

# 3. 检查swarm.pem文件
echo_yellow "\n🔐 3. 检查节点身份文件..."
if [ -f "swarm.pem" ]; then
    echo_green "✅ swarm.pem 文件存在"
    
    # 获取peer ID
    if command -v python3 &> /dev/null; then
        PEER_ID=$(python3 -c "
import hivemind
dht = hivemind.DHT(start=False, identity_path='swarm.pem')
print(str(dht.peer_id))
" 2>/dev/null || echo "无法获取")
        
        if [ "$PEER_ID" != "无法获取" ]; then
            echo_green "✅ Peer ID: $PEER_ID"
        else
            echo_yellow "⚠️  无法从swarm.pem读取Peer ID"
        fi
    fi
else
    echo_yellow "⚠️  swarm.pem 文件不存在，将在首次运行时生成"
fi

# 4. 检查进程状态
echo_yellow "\n🏃 4. 检查节点运行状态..."
if pgrep -f "python.*train_single_gpu" > /dev/null; then
    echo_green "✅ 训练进程正在运行"
    
    # 显示进程信息
    PROCESS_COUNT=$(pgrep -f "python.*train_single_gpu" | wc -l)
    echo "   运行中的训练进程数: $PROCESS_COUNT"
    
    # 检查最新日志
    if [ -d "logs" ]; then
        LATEST_LOG=$(find logs -name "*.log" -type f -exec ls -t {} + | head -1)
        if [ -n "$LATEST_LOG" ]; then
            echo "   最新日志文件: $LATEST_LOG"
            
            # 检查注册信息
            if grep -q "Registering self with peer ID" "$LATEST_LOG" 2>/dev/null; then
                echo_green "   ✅ 在日志中找到注册信息"
                LAST_REGISTER=$(grep "Registering self with peer ID" "$LATEST_LOG" | tail -1)
                echo "   $LAST_REGISTER"
            else
                echo_yellow "   ⚠️  日志中未找到注册信息"
            fi
            
            # 检查错误信息
            ERROR_COUNT=$(grep -i "error\|exception" "$LATEST_LOG" 2>/dev/null | wc -l || echo 0)
            if [ "$ERROR_COUNT" -gt 0 ]; then
                echo_red "   ❌ 发现 $ERROR_COUNT 个错误"
                echo "   最近的错误:"
                grep -i "error\|exception" "$LATEST_LOG" | tail -3
            fi
        fi
    fi
else
    echo_red "❌ 没有发现运行中的训练进程"
    echo "请运行: ./manage.sh 启动节点"
fi

# 5. 检查网络连接
echo_yellow "\n🌐 5. 检查网络连接..."

# 检查Gensyn测试网连接
if curl -s "https://gensyn-testnet.g.alchemy.com/public" > /dev/null 2>&1; then
    echo_green "✅ Gensyn测试网连接正常"
else
    echo_red "❌ 无法连接到Gensyn测试网"
fi

# 检查仪表板连接
if curl -s "https://dashboard-math-hard.gensyn.ai/" > /dev/null 2>&1; then
    echo_green "✅ 仪表板网站连接正常"
else
    echo_red "❌ 无法连接到仪表板网站"
fi

# 6. 检查链上注册状态
echo_yellow "\n⛓️  6. 检查链上注册状态..."
if [ -n "$PEER_ID" ] && [ "$PEER_ID" != "无法获取" ]; then
    # 这里需要调用智能合约查询
    echo_blue "   Peer ID: $PEER_ID"
    echo "   正在查询链上注册状态..."
    
    # 检查区块链浏览器
    echo "   可以在以下网址查看链上活动:"
    echo "   https://gensyn-testnet.explorer.alchemy.com/address/0x2fC68a233EF9E9509f034DD551FF90A79a0B8F82?tab=logs"
fi

# 7. 生成建议
echo_yellow "\n💡 7. 故障排除建议..."

echo_blue "如果节点在仪表板上不显示，请尝试以下步骤:"

echo "1. 确保节点已正确启动并完成注册:"
echo "   ./manage.sh"

echo -e "\n2. 检查注册是否成功完成:"
echo "   grep -r \"Registering self with peer ID\" logs/"

echo -e "\n3. 如果注册失败，尝试删除swarm.pem并重新启动:"
echo "   rm -f swarm.pem"
echo "   ./manage.sh"

echo -e "\n4. 检查节点是否被排行榜收录 (可能需要几分钟):"
echo "   https://dashboard-math-hard.gensyn.ai/"

echo -e "\n5. 查看详细日志:"
echo "   tail -f logs/*.log"

echo -e "\n6. 如果问题持续，检查以下可能的原因:"
echo "   - 网络连接问题"
echo "   - 节点性能不足被跳过轮次"
echo "   - 训练质量不达标"
echo "   - 同一IP多节点可能降权"

echo_blue "\n🎯 关键提醒:"
echo "- 节点可能需要几分钟才会在仪表板显示"
echo "- 排行榜只显示有奖励记录的活跃节点"  
echo "- 检查您的动物昵称而不是Peer ID"

# 8. 实时监控建议
echo_yellow "\n📊 8. 实时监控建议..."
echo "建议使用项目内置的监控系统:"
echo "   ./ops_full_manager.sh"
echo ""
echo "或者查看Web界面 (如果可用):"
echo "   http://localhost:3000"

echo_green "\n✨ 诊断完成！"
echo "如果问题仍然存在，请提供上述检查结果以便进一步诊断。" 