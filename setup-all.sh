#!/bin/bash
set -e

# 颜色定义
CHECK_MARK="\033[1;32m✔\033[0m"
CROSS_MARK="\033[1;31m✘\033[0m"
YELLOW_TEXT="\033[1;33m"
GREEN_TEXT="\033[1;32m"
BLUE_TEXT="\033[1;34m"
RED_TEXT="\033[1;31m"
PURPLE_TEXT="\033[1;35m"
RESET_TEXT="\033[0m"

# 颜色输出函数定义
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

echo_purple() {
    echo -e "$PURPLE_TEXT$1$RESET_TEXT"
}

# 配置变量
# 检测现有的 rl-swarm 目录
if [ -d "$HOME/rl-swarm" ]; then
    INSTALL_DIR="$HOME"
    SWARM_DIR="$HOME/rl-swarm"
    echo_green "检测到现有的 rl-swarm 仓库: $SWARM_DIR"
else
    INSTALL_DIR="$HOME/rl-swarm-setup"
    SWARM_DIR="$INSTALL_DIR/rl-swarm"
fi
NEXUS_CONFIG_DIR="$HOME/.nexus"
NODE_ID_FILE="$NEXUS_CONFIG_DIR/node_id"

# 显示标题
clear
echo_blue "
██████  ██       ███████ ██     ██  █████  ██████  ███    ███
██   ██ ██       ██      ██     ██ ██   ██ ██   ██ ████  ████ 
██████  ██       ███████ ██  █  ██ ███████ ██████  ██ ████ ██ 
██   ██ ██            ██ ██ ███ ██ ██   ██ ██   ██ ██  ██  ██ 
██   ██ ███████  ███████  ███ ███  ██   ██ ██   ██ ██      ██ 
                                                               
           +  NEXUS NETWORK 统一安装脚本                      
"

echo_purple "=== Gensyn RL Swarm + Nexus Network 一键安装部署 ==="
echo_yellow "本脚本将自动完成以下任务："
echo "  📦 安装系统依赖 (Homebrew, Screen, Python 3.12)"
echo "  🔧 配置开发环境 (虚拟环境, 环境变量)"
echo "  📥 下载和安装 Gensyn RL Swarm"
echo "  🌐 下载和安装 Nexus Network"
echo "  🚀 启动监控和管理脚本"
echo ""

# 确认继续
read -p "是否继续安装？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_yellow "安装已取消"
    exit 0
fi

# 创建安装目录
echo_blue "\n🔧 准备安装环境..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 检查操作系统
check_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo_green "检测到 macOS 系统"
        OS_TYPE="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo_green "检测到 Linux 系统"
        OS_TYPE="linux"
    else
        echo_red "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# Homebrew 环境变量自动设置和永久化 (macOS)
setup_homebrew_env() {
    if [[ "$OS_TYPE" != "macos" ]]; then
        return 0
    fi
    
    local shell_config=""
    local brew_shellenv_cmd=""
    
    # 确定当前使用的 shell 配置文件
    if [[ "$SHELL" == */zsh ]]; then
        shell_config="$HOME/.zshrc"
    elif [[ "$SHELL" == */bash ]]; then
        shell_config="$HOME/.bashrc"
    else
        shell_config="$HOME/.profile"
    fi
    
    # 检测 Homebrew 安装路径
    if [ -d "/opt/homebrew/bin" ]; then
        brew_shellenv_cmd='eval "$(/opt/homebrew/bin/brew shellenv)"'
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -d "/usr/local/bin" ]; then
        brew_shellenv_cmd='eval "$(/usr/local/bin/brew shellenv)"'
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    
    # 检查配置文件中是否已包含 Homebrew 环境设置
    if [ -n "$brew_shellenv_cmd" ] && [ -f "$shell_config" ]; then
        if ! grep -q "brew shellenv" "$shell_config"; then
            echo "# Homebrew environment setup" >> "$shell_config"
            echo "$brew_shellenv_cmd" >> "$shell_config"
            echo -e "[环境变量] 已添加到 $shell_config $CHECK_MARK"
        else
            echo -e "[环境变量] 已存在于 $shell_config $CHECK_MARK"
        fi
    elif [ -n "$brew_shellenv_cmd" ]; then
        echo "# Homebrew environment setup" > "$shell_config"
        echo "$brew_shellenv_cmd" >> "$shell_config"
        echo -e "[环境变量] 已创建 $shell_config $CHECK_MARK"
    fi
}

# 安装系统依赖
install_system_dependencies() {
    echo_blue "\n📦 安装系统依赖..."
    
    if [[ "$OS_TYPE" == "macos" ]]; then
        # macOS 使用 Homebrew
        if ! command -v brew &> /dev/null; then
            echo_yellow "安装 Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            setup_homebrew_env
        else
            echo -e "[Homebrew] 已安装 $CHECK_MARK"
        fi
        
        # 安装 screen
        if ! command -v screen &> /dev/null; then
            echo_yellow "安装 screen..."
            brew install screen
        else
            echo -e "[screen] 已安装 $CHECK_MARK"
        fi
        
        # 安装 Python 3.12
        if ! brew list python@3.12 &> /dev/null; then
            echo_yellow "安装 Python 3.12..."
            brew install python@3.12
        else
            echo -e "[Python 3.12] 已安装 $CHECK_MARK"
        fi
        
        # 设置 Python 路径
        PY312_PATH="$(brew --prefix python@3.12)/bin"
        export PATH="$PY312_PATH:$PATH"
        
        # 检查 python3 链接
        PYVER=$(python3 --version 2>/dev/null || echo "none")
        if [[ "$PYVER" != "Python 3.12"* ]]; then
            echo_yellow "设置 python3 指向 Python 3.12..."
            sudo mkdir -p /usr/local/bin
            sudo ln -sf "$PY312_PATH/python3.12" /usr/local/bin/python3
        fi
        
    elif [[ "$OS_TYPE" == "linux" ]]; then
        # Linux 使用包管理器
        if command -v apt-get &> /dev/null; then
            echo_yellow "更新软件包列表..."
            sudo apt-get update
            
            echo_yellow "安装依赖包..."
            sudo apt-get install -y screen python3 python3-pip python3-venv git curl expect
        elif command -v yum &> /dev/null; then
            echo_yellow "安装依赖包..."
            sudo yum install -y screen python3 python3-pip git curl expect
        else
            echo_red "不支持的 Linux 发行版"
            exit 1
        fi
    fi
    
    # 验证安装
    if command -v screen &> /dev/null; then
        SCREEN_VERSION=$(screen -v | head -n1 || echo "unknown")
        echo -e "[screen] 版本：$SCREEN_VERSION $CHECK_MARK"
    else
        echo -e "[screen] 安装失败 $CROSS_MARK"
        exit 1
    fi
}

# 安装 Gensyn RL Swarm
install_gensyn() {
    echo_blue "\n🤖 配置 Gensyn RL Swarm..."
    
    # 检查仓库是否存在
    if [ ! -d "$SWARM_DIR" ]; then
        echo_yellow "克隆 RL Swarm 仓库到 $SWARM_DIR..."
        mkdir -p "$(dirname "$SWARM_DIR")"
        cd "$(dirname "$SWARM_DIR")"
        git clone https://github.com/gensyn-ai/rl-swarm
    else
        echo -e "[RL Swarm 仓库] 使用现有仓库 $SWARM_DIR $CHECK_MARK"
        # 更新现有仓库
        cd "$SWARM_DIR"
        echo_yellow "更新现有仓库..."
        git pull origin main 2>/dev/null || echo_yellow "仓库更新跳过（可能有未提交的更改）"
    fi
    
    cd "$SWARM_DIR"
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        echo_yellow "创建 Python 虚拟环境..."
        python3 -m venv venv
    else
        echo -e "[虚拟环境] 已存在 $CHECK_MARK"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 修复依赖冲突问题
    echo_yellow "修复已知依赖冲突..."
    pip install --force-reinstall transformers==4.51.3 trl==0.19.1
    echo -e "[依赖修复] 完成 $CHECK_MARK"
    
    # 设置 macOS 特定环境变量
    if [[ "$OS_TYPE" == "macos" ]]; then
        export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
        export PYTORCH_ENABLE_MPS_FALLBACK=1
        echo -e "[macOS 环境变量] 设置完成 $CHECK_MARK"
    fi
    
    echo -e "[Gensyn RL Swarm] 安装完成 $CHECK_MARK"
    cd ..
}

# 安装 Nexus Network
install_nexus() {
    echo_blue "\n🌐 安装 Nexus Network..."
    
    # 创建 Nexus 配置目录
    mkdir -p "$NEXUS_CONFIG_DIR"
    
    # 检查是否已安装
    if command -v nexus-cli &> /dev/null; then
        local version=$(nexus-cli --version 2>/dev/null || echo "unknown")
        echo -e "[Nexus CLI] 已安装 (版本: $version) $CHECK_MARK"
    else
        echo_yellow "下载并安装 Nexus CLI..."
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
        fi
    fi
    
    # 设置 Node ID
    if [ ! -f "$NODE_ID_FILE" ]; then
        echo_yellow "\n首次运行，需要设置 Nexus Node ID"
        echo_yellow "请输入您的 Node ID（例如：35915268）："
        read -p "Node ID: " NODE_ID
        
        if [ -z "$NODE_ID" ]; then
            echo_red "Node ID 不能为空，跳过 Nexus 配置"
        else
            echo "$NODE_ID" > "$NODE_ID_FILE"
            echo -e "[Node ID] 已保存到 $NODE_ID_FILE $CHECK_MARK"
        fi
    else
        NODE_ID=$(cat "$NODE_ID_FILE")
        echo -e "[Node ID] 已保存: $NODE_ID $CHECK_MARK"
    fi
}

# 创建快捷启动脚本
create_launcher_scripts() {
    echo_blue "\n🚀 创建启动脚本..."
    
    cd "$INSTALL_DIR"
    
    # 创建 Gensyn 启动脚本
    cat > start-gensyn.sh << EOF
#!/bin/bash
cd "$SWARM_DIR"
source venv/bin/activate
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_ENABLE_MPS_FALLBACK=1
echo "🚀 启动 Gensyn RL Swarm..."
# 修复可能的依赖冲突
echo "🔧 检查并修复依赖..."
pip install --force-reinstall transformers==4.51.3 trl==0.19.1 >/dev/null 2>&1
./run_rl_swarm.sh
EOF
    chmod +x start-gensyn.sh
    
    # 创建 Nexus 启动脚本
    if [ -f "$NODE_ID_FILE" ]; then
        NODE_ID=$(cat "$NODE_ID_FILE")
        cat > start-nexus.sh << EOF
#!/bin/bash
echo "🌐 启动 Nexus Network..."
nexus-cli start --node-id $NODE_ID
EOF
        chmod +x start-nexus.sh
    fi
    
    # 创建监控脚本启动器
    cat > start-monitoring.sh << EOF
#!/bin/bash
cd "$SWARM_DIR"
echo "📊 选择要启动的监控脚本："
echo "1. RL Swarm 监控 (auto-run.sh)"
echo "2. Nexus 监控 (auto-nexus.sh)"
echo "3. 同时启动两个监控"
read -p "请选择 (1-3): " choice

case \$choice in
    1)
        echo "启动 RL Swarm 监控..."
        ./auto-run.sh
        ;;
    2)
        echo "启动 Nexus 监控..."
        ./auto-nexus.sh
        ;;
    3)
        echo "同时启动两个监控..."
        ./auto-run.sh &
        ./auto-nexus.sh &
        wait
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
EOF
    chmod +x start-monitoring.sh
    
    echo -e "[启动脚本] 创建完成 $CHECK_MARK"
}

# 显示完成信息
show_completion_info() {
    echo_green "\n🎉 安装完成！"
    echo_purple "\n=== 快捷启动命令 ==="
    echo_blue "进入安装目录："
    echo "  cd $INSTALL_DIR"
    echo ""
    
    echo_blue "启动 Gensyn RL Swarm："
    echo "  ./start-gensyn.sh"
    echo "  # 或者手动："
    echo "  cd $SWARM_DIR && source venv/bin/activate && ./run_rl_swarm.sh"
    echo ""
    
    if [ -f "$NODE_ID_FILE" ]; then
        echo_blue "启动 Nexus Network："
        echo "  ./start-nexus.sh"
        NODE_ID=$(cat "$NODE_ID_FILE")
        echo "  # 或者手动："
        echo "  nexus-cli start --node-id $NODE_ID"
        echo ""
    fi
    
    echo_blue "启动监控脚本："
    echo "  ./start-monitoring.sh"
    echo ""
    
    echo_purple "=== 会话管理 ==="
    echo_blue "查看 Screen 会话："
    echo "  screen -list"
    echo ""
    echo_blue "连接到会话："
    echo "  screen -r gensyn    # RL Swarm"
    echo "  screen -r nexus     # Nexus"
    echo ""
    echo_blue "从会话中分离："
    echo "  Ctrl+A, D"
    echo ""
    
    echo_purple "=== 日志文件 ==="
    echo "  RL Swarm 日志:     $SWARM_DIR/logs/swarm_launcher.log"
    echo "  监控日志:         $SWARM_DIR/auto_monitor.log"
    echo "  Nexus 监控日志:    $SWARM_DIR/nexus_monitor.log"
    echo ""
    
    echo_yellow "💡 提示：首次运行 RL Swarm 时需要在浏览器中完成身份认证"
    echo_yellow "💡 提示：所有服务都在后台 screen 会话中运行，即使关闭终端也会继续"
}

# 主安装流程
main() {
    echo_blue "开始安装流程..."
    
    # 检查操作系统
    check_os
    
    # 安装系统依赖
    install_system_dependencies
    
    # 安装 Gensyn RL Swarm
    install_gensyn
    
    # 安装 Nexus Network
    install_nexus
    
    # 创建启动脚本
    create_launcher_scripts
    
    # 显示完成信息
    show_completion_info
    
    echo_green "\n✨ 所有组件安装完成！您现在可以开始使用 Gensyn 和 Nexus 了！"
}

# 错误处理
trap 'echo_red "\n❌ 安装过程中发生错误，请检查上面的错误信息"; exit 1' ERR

# 运行主程序
main "$@"