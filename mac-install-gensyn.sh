#!/bin/bash
set -e

CHECK_MARK="\033[1;32m✔\033[0m"
CROSS_MARK="\033[1;31m✘\033[0m"

# Homebrew 环境变量自动设置和永久化
setup_homebrew_env() {
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
        # 如果配置文件不存在，创建它
        echo "# Homebrew environment setup" > "$shell_config"
        echo "$brew_shellenv_cmd" >> "$shell_config"
        echo -e "[环境变量] 已创建 $shell_config $CHECK_MARK"
    fi
}

if ! command -v brew &> /dev/null; then
    setup_homebrew_env
fi

# 1. 检查并安装 Homebrew
if command -v brew &> /dev/null; then
    echo -e "[Homebrew] 已安装 $CHECK_MARK"
else
    echo "未检测到 Homebrew，正在安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # 安装后设置环境变量并永久化
    setup_homebrew_env
    echo -e "[Homebrew] 安装完成 $CHECK_MARK"
fi

# 2. 检查并安装 screen
if command -v screen &> /dev/null; then
    echo -e "[screen] 已安装 $CHECK_MARK"
else
    echo "正在使用 Homebrew 安装 screen..."
    brew install screen
    echo -e "[screen] 安装完成 $CHECK_MARK"
fi

# 验证 screen 是否可以正常使用
if command -v screen &> /dev/null; then
    SCREEN_VERSION=$(screen -v | head -n1 || echo "unknown")
    echo -e "[screen] 版本：$SCREEN_VERSION $CHECK_MARK"
else
    echo -e "[screen] 安装后仍无法找到，可能需要重启终端 $CROSS_MARK"
    echo -e "请运行以下命令后重新执行脚本："
    if [[ "$SHELL" == */zsh ]]; then
        echo -e "  source ~/.zshrc"
    elif [[ "$SHELL" == */bash ]]; then
        echo -e "  source ~/.bashrc"
    else
        echo -e "  source ~/.profile"
    fi
fi

# 3. 检查并安装 python@3.12
if brew list python@3.12 &> /dev/null; then
    echo -e "[python@3.12] 已安装 $CHECK_MARK"
else
    echo "正在使用 Homebrew 安装 python@3.12..."
    brew install python@3.12
    echo -e "[python@3.12] 安装完成 $CHECK_MARK"
fi

PY312_PATH="$(brew --prefix python@3.12)/bin"
export PATH="$PY312_PATH:$PATH"

# 4. 检查 python3 是否指向 python3.12
PYVER=$(python3 --version 2>/dev/null || echo "none")
if [[ "$PYVER" == "Python 3.12"* ]]; then
    echo -e "[python3 指向 python3.12] 已设置 $CHECK_MARK"
else
    echo "将 python3 指向 python3.12..."
    # 自动创建 /usr/local/bin 目录（如不存在）
    sudo mkdir -p /usr/local/bin
    sudo ln -sf "$PY312_PATH/python3.12" /usr/local/bin/python3
    echo -e "[python3 指向 python3.12] 设置完成 $CHECK_MARK"
fi

# 5. 检查并克隆仓库
if [ -d "rl-swarm" ]; then
    echo -e "[仓库已存在] $CHECK_MARK"
else
    git clone https://github.com/gensyn-ai/rl-swarm
    echo -e "[仓库克隆完成] $CHECK_MARK"
fi
cd rl-swarm

# 6. 检查并创建虚拟环境
if [ -d "venv" ]; then
    echo -e "[虚拟环境已存在] $CHECK_MARK"
else
    python3 -m venv venv
    echo -e "[虚拟环境创建完成] $CHECK_MARK"
fi
source venv/bin/activate

# 修复已知依赖冲突问题
echo "修复已知依赖冲突..."
pip install --force-reinstall transformers==4.51.3 trl==0.19.1
echo -e "[依赖修复] 完成 $CHECK_MARK"

# 7. 设置环境变量并运行脚本
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_ENABLE_MPS_FALLBACK=1
echo -e "[环境变量设置完成] $CHECK_MARK"

echo -e "\n📱 提示：训练开始后，您可以使用以下命令管理训练会话："
echo -e "  - screen -r gensyn  # 重新连接到训练会话"
echo -e "  - Ctrl+A, D        # 从会话中分离（训练继续在后台运行）"
echo -e "  - ./auto-run.sh    # 启动自动监控和重启脚本\n"

./run_rl_swarm.sh 
