# RL Swarm & Nexus 项目脚本说明文档

## 概述

本项目包含多个核心脚本，用于 RL Swarm 强化学习项目和 Nexus 网络项目的安装、配置、管理和启动。这些脚本提供了完整的自动化解决方案，从环境搭建到持续监控，再到一键启动工作环境。

---

## 📁 脚本列表

### 🚀 启动管理脚本
6. **[launch-all.sh](#6-launch-allsh)** - 🌟 RL Swarm 完整工作环境一键启动脚本（推荐）
7. **[quick-launch.sh](#7-quick-launchsh)** - 快速启动脚本，无确认直接启动4窗口
8. **[workspace-layout.sh](#8-workspace-layoutsh)** - 智能多终端布局管理脚本
9. **[LAUNCH_GUIDE.md](#9-launch_guidemd)** - 启动脚本详细使用指南

### 🔧 核心管理脚本
1. **[setup-all.sh](#1-setup-allsh)** - 🌟 Gensyn + Nexus 统一安装脚本（推荐）
2. **[mac-install-gensyn.sh](#2-mac-install-gensynsh)** - macOS 环境 RL Swarm 一键安装脚本
3. **[auto-run.sh](#3-auto-runsh)** - RL Swarm 自动监控和重启脚本
4. **[install-nexus.sh](#4-install-nexussh)** - Nexus Network 安装和管理脚本
5. **[auto-nexus.sh](#5-auto-nexussh)** - Nexus 自动监控脚本

---

## 1. setup-all.sh

### 功能描述
🌟 **最新推荐脚本** - 统一的 Gensyn RL Swarm + Nexus Network 一键安装部署脚本，支持跨平台自动化安装。

### 主要功能
- ✅ **跨平台支持**：自动识别 macOS/Linux 并使用对应包管理器
- ✅ **统一安装**：一键安装 Gensyn 和 Nexus 所有组件
- ✅ **智能配置**：自动处理环境变量、依赖关系、配置文件
- ✅ **快捷启动**：自动创建便捷的启动脚本
- ✅ **监控集成**：整合现有监控脚本，提供统一管理

### 安装流程
1. **🔍 系统检测**：自动识别操作系统类型
2. **📦 依赖安装**：Homebrew/apt、Screen、Python 3.12
3. **🔧 环境配置**：PATH 设置、shell 配置文件更新
4. **🤖 Gensyn 安装**：克隆仓库、创建虚拟环境
5. **🌐 Nexus 安装**：下载 CLI、配置 Node ID
6. **🚀 脚本创建**：生成快捷启动和监控脚本

### 使用方法
```bash
# 下载并运行统一安装脚本
curl -O https://your-repo/setup-all.sh
chmod +x setup-all.sh
./setup-all.sh
```

### 安装后的快捷命令
```bash
# 进入安装目录
cd ~/rl-swarm-setup

# 启动 Gensyn RL Swarm
./start-gensyn.sh

# 启动 Nexus Network
./start-nexus.sh

# 启动监控脚本（交互式选择）
./start-monitoring.sh
```

### 目录结构
```
~/rl-swarm-setup/
├── rl-swarm/              # Gensyn RL Swarm 项目
│   ├── venv/              # Python 虚拟环境
│   ├── auto-run.sh        # RL Swarm 监控脚本
│   └── run_rl_swarm.sh    # RL Swarm 启动脚本
├── start-gensyn.sh        # Gensyn 快捷启动
├── start-nexus.sh         # Nexus 快捷启动
└── start-monitoring.sh    # 监控脚本启动器
```

### 特色功能
- 🎯 **自动化安装**：使用 expect 自动确认 Nexus 安装
- 🔧 **智能配置**：自动检测 shell 类型并更新配置文件
- 📊 **监控集成**：集成现有的监控脚本，提供统一管理界面
- 🌍 **跨平台兼容**：支持 macOS（Homebrew）和 Linux（apt/yum）

---

## 2. mac-install-gensyn.sh

### 功能描述
专为 macOS 系统设计的 RL Swarm 一键安装脚本，自动处理所有依赖项安装和环境配置。

### 主要功能
- ✅ **Homebrew 管理**：自动安装 Homebrew 并永久化环境变量
- ✅ **Screen 安装**：安装并配置 screen 终端复用器
- ✅ **Python 3.12**：安装并配置 Python 3.12 环境
- ✅ **项目克隆**：自动克隆 RL Swarm 仓库
- ✅ **虚拟环境**：创建并激活 Python 虚拟环境
- ✅ **环境变量**：设置 macOS 特定的 PyTorch 环境变量

### 使用方法
```bash
# 下载并运行安装脚本
curl -O https://your-repo/mac-install-gensyn.sh
chmod +x mac-install-gensyn.sh
./mac-install-gensyn.sh
```

### 安装流程
1. **环境检查**：检测并安装 Homebrew
2. **依赖安装**：screen、Python 3.12
3. **项目准备**：克隆仓库、创建虚拟环境
4. **环境配置**：设置 macOS 特定环境变量
5. **启动训练**：自动运行 RL Swarm

### 环境变量设置
```bash
# macOS 内存优化
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_ENABLE_MPS_FALLBACK=1

# Homebrew 路径（自动添加到 shell 配置）
eval "$(/opt/homebrew/bin/brew shellenv)"  # Apple Silicon
eval "$(/usr/local/bin/brew shellenv)"     # Intel Mac
```

### 安装后管理
```bash
# 重新连接到训练会话
screen -r gensyn

# 从会话中分离（保持后台运行）
Ctrl+A, D

# 启动自动监控
./auto-run.sh
```

---

## 3. auto-run.sh

### 功能描述
RL Swarm 智能监控脚本，提供 24/7 自动监控、异常检测和自动重启功能。

### 主要功能
- 🔄 **智能监控**：实时监控训练进程状态
- 🛠️ **自动重启**：检测异常自动重启训练
- 🧹 **进程清理**：自动清理僵尸进程和端口占用
- 📊 **状态报告**：详细的进程状态信息
- ⏰ **定时检查**：每 5 分钟检查一次状态

### 监控指标
```bash
# 进程监控
- swarm_launcher 父子进程（需要 2 个）
- run_rl_swarm.sh 主脚本进程
- p2pd 点对点通信进程
- node.js 身份管理服务

# 异常检测
- 进程数量异常
- 日志错误信息
- 日志长时间未更新（>1小时）
- 端口占用异常
```

### 使用方法
```bash
# 启动监控（前台运行）
./auto-run.sh

# 后台运行监控
nohup ./auto-run.sh &

# 查看监控日志
tail -f auto_monitor.log
```

### 自动重启流程
1. **异常检测**：发现进程异常或日志错误
2. **进程清理**：清理相关 Python、node、p2pd 进程
3. **端口释放**：释放被占用的 3000 端口
4. **日志清空**：清空训练日志文件
5. **重新启动**：在 screen 会话中重启训练

### 配置参数
```bash
SESSION_NAME="gensyn"           # Screen 会话名称
MONITOR_INTERVAL=300            # 监控间隔（秒）
RL_LOG_FILE="logs/swarm_launcher.log"  # 训练日志文件
```

---

## 4. install-nexus.sh

### 功能描述
Nexus Network 完整管理脚本，提供安装、配置、启动和管理的一站式解决方案。

### 主要功能
- 🚀 **自动安装**：一键安装 Nexus CLI
- 🔑 **ID 管理**：Node ID 一次设置，永久保存
- 📺 **Screen 管理**：后台会话管理和监控
- 🎛️ **交互界面**：友好的菜单式操作界面
- 📊 **状态监控**：实时显示运行状态

### 使用方法

#### 交互式菜单模式
```bash
./install-nexus.sh

# 菜单选项：
# 1. 安装 Nexus CLI
# 2. 设置/更新 Node ID  
# 3. 启动 Nexus Network
# 4. 停止 Nexus Network
# 5. 查看状态
# 6. 连接到 Screen 会话
# 7. 退出
```

#### 命令行模式
```bash
# 安装 Nexus CLI
./install-nexus.sh install

# 启动 Nexus Network
./install-nexus.sh start

# 停止 Nexus Network
./install-nexus.sh stop

# 查看状态
./install-nexus.sh status

# 连接到 screen 会话
./install-nexus.sh connect
```

### 安装流程
1. **依赖检查**：检查 screen 是否可用
2. **CLI 安装**：执行 `curl https://cli.nexus.xyz/ | sh`
3. **自动确认**：使用 expect 自动输入 'y' 确认
4. **环境配置**：添加 nexus 到 PATH
5. **Node ID 设置**：首次运行时设置并保存 Node ID

### 配置管理
```bash
# 配置文件位置
~/.nexus/node_id              # Node ID 存储文件

# Screen 会话管理
screen -r nexus               # 连接到 Nexus 会话
Ctrl+A, D                     # 从会话中分离
screen -list                  # 查看所有会话
```

### 状态显示
- ✅ Nexus CLI 安装状态和版本
- ✅ Node ID 配置状态
- ✅ 进程运行状态和 PID
- ✅ Screen 会话状态

---

## 5. auto-nexus.sh

### 功能描述
Nexus Network 专业级监控脚本，提供企业级的进程监控和自动恢复能力。

### 主要功能
- 🔍 **多层检测**：4 种方式检测进程状态
- 🔄 **自动重启**：最多 999 次自动重启
- 📋 **详细日志**：完整的操作日志记录
- ⏰ **定时监控**：每 10 分钟检查一次
- 🛠️ **智能恢复**：清理死会话后重启

### 进程检测方式
```bash
# 方法1：检查主要 nexus-cli 进程
ps aux | grep "nexus-cli start" | grep -v grep

# 方法2：检查 screen 会话中的进程
ps aux | grep "bash -c nexus-cli start" | grep -v grep

# 方法3：检查 screen 管理进程
ps aux | grep "SCREEN -dmS nexus" | grep -v grep

# 方法4：使用 pgrep 备用检查
pgrep -f "nexus-cli start"
```

### 使用方法
```bash
# 启动监控
./auto-nexus.sh

# 查看监控日志
tail -f nexus_monitor.log
```

### 配置参数
```bash
PROCESS_NAME="nexus-network"        # 进程名称
SCREEN_SESSION="nexus"              # Screen 会话名称
START_CMD="nexus-cli start --node-id 35915268"  # 启动命令
CHECK_INTERVAL=600                  # 监控间隔（10分钟）
MAX_RESTARTS=999                    # 最大重启次数
```

### 监控流程
1. **状态检查**：多方式检测进程状态
2. **会话管理**：创建和清理 screen 会话
3. **进程启动**：在会话中启动 Nexus
4. **状态验证**：验证启动是否成功
5. **持续监控**：定时检查和自动恢复

---

## 🔧 系统要求

### 基础要求
- **操作系统**：macOS 10.15+ 或 Linux
- **内存**：最低 32GB RAM（CPU 模式）
- **存储**：至少 10GB 可用空间
- **网络**：稳定的互联网连接

### 软件依赖
- **Git**：版本控制
- **Curl**：下载脚本和工具
- **Python 3.10+**：RL Swarm 运行环境（推荐 3.12）
- **Node.js**：身份管理服务
- **Screen**：终端复用器
- **Homebrew**：macOS 包管理器（macOS 用户）
- **apt/yum**：Linux 包管理器（Linux 用户）

---

## 🚀 快速开始

### 方案一：RL Swarm + Nexus 统一部署（推荐）
```bash
# 使用新的统一安装脚本（推荐）
curl -O https://your-repo/setup-all.sh
chmod +x setup-all.sh
./setup-all.sh

# 安装后使用新的启动脚本
cd ~/rl-swarm-setup
./start-gensyn.sh     # 启动 Gensyn
./start-nexus.sh      # 启动 Nexus
./start-monitoring.sh # 启动监控

# 或者使用一键启动工作环境
cd /Users/mrw/rl-swarm
./launch-all.sh       # 完整启动（带说明）
./quick-launch.sh     # 快速启动（日常使用）
```

### 方案二：RL Swarm 单独快速部署
```bash
# 1. 下载并运行 macOS 安装脚本
curl -O https://your-repo/mac-install-gensyn.sh
chmod +x mac-install-gensyn.sh
./mac-install-gensyn.sh

# 2. 启动自动监控（可选）
./auto-run.sh
```

### 方案三：Nexus Network 单独快速部署
```bash
# 1. 安装 Nexus
./install-nexus.sh install

# 2. 启动 Nexus
./install-nexus.sh start

# 3. 启动监控（可选）
./auto-nexus.sh
```

---

## 🛠️ 故障排除

### 常见问题

#### 1. Screen 命令未找到
```bash
# 手动安装 screen
brew install screen

# 重新加载环境变量
source ~/.zshrc  # 或 ~/.bashrc
```

#### 2. Python 版本不正确
```bash
# 检查 Python 版本
python3 --version

# 重新链接 Python
sudo ln -sf /opt/homebrew/bin/python3.12 /usr/local/bin/python3
```

#### 3. 进程启动失败
```bash
# 检查日志
tail -f logs/swarm_launcher.log  # RL Swarm
tail -f nexus_monitor.log        # Nexus

# 手动重启
screen -r gensyn    # RL Swarm
screen -r nexus     # Nexus
```

#### 4. 端口占用
```bash
# 查看端口占用
lsof -ti:3000

# 释放端口
kill -9 $(lsof -ti:3000)
```

### 日志文件位置
```bash
# 统一安装后的日志位置
~/rl-swarm-setup/rl-swarm/logs/swarm_launcher.log    # 训练日志
~/rl-swarm-setup/rl-swarm/logs/yarn.log              # Node.js 服务日志
~/rl-swarm-setup/rl-swarm/auto_monitor.log           # RL Swarm 监控日志
~/rl-swarm-setup/rl-swarm/nexus_monitor.log          # Nexus 监控日志
~/.nexus/node_id                                      # Node ID 配置

# 传统安装的日志位置
logs/swarm_launcher.log          # 训练日志
logs/yarn.log                    # Node.js 服务日志
auto_monitor.log                 # 监控脚本日志
nexus_monitor.log                # Nexus 监控日志
~/.nexus/node_id                 # Node ID 配置
```

---

## 📞 技术支持

### 社区支持
- **Discord**：[Gensyn Discord](https://discord.gg/AdnyWNzXh5)
- **GitHub Issues**：项目仓库 Issues 页面
- **文档**：[官方文档](https://github.com/gensyn-ai/rl-swarm)

### 高级配置
- **GPU 支持**：RTX 3090/4090/5090、A100、H100
- **分布式训练**：Hivemind 框架
- **链上身份**：Alchemy 管理
- **监控仪表板**：dashboard.gensyn.ai

---

## 📄 许可证

本项目遵循开源许可证，详情请查看项目根目录的 LICENSE 文件。

---

---

## 6. launch-all.sh

### 功能描述
🌟 **最新推荐启动脚本** - RL Swarm 完整工作环境一键启动脚本，自动打开4个优化布局的终端窗口。

### 主要功能
- ✅ **一键启动**：自动启动完整的4窗口工作环境
- ✅ **智能布局**：2x2网格布局，窗口位置和大小优化
- ✅ **Screen管理**：自动创建或连接现有screen会话
- ✅ **监控集成**：自动启动对应的监控脚本
- ✅ **详细说明**：提供完整的使用指南和操作提示

### 窗口布局
```
┌─────────────┬─────────────┐
│ 🤖 Gensyn   │ 📊 Gensyn   │
│    训练     │    监控     │
├─────────────┼─────────────┤
│ 🌐 Nexus    │ 📈 Nexus    │
│   运行      │   监控      │
└─────────────┴─────────────┘
```

### 使用方法
```bash
# 给脚本添加执行权限
chmod +x launch-all.sh

# 启动完整工作环境
./launch-all.sh
```

---

## 7. quick-launch.sh

### 功能描述
快速启动脚本，无确认提示直接启动4个终端窗口，适合日常使用。

### 主要功能
- ⚡ **极速启动**：无确认直接启动
- 🎯 **4窗口布局**：训练+监控的完整环境
- 🔄 **会话复用**：智能连接现有screen会话
- 📊 **监控自启**：自动运行监控脚本

### 使用方法
```bash
# 日常快速启动（推荐）
./quick-launch.sh
```

---

## 8. workspace-layout.sh

### 功能描述
智能多终端布局管理脚本，提供灵活的窗口布局选择和管理功能。

### 主要功能
- 🎨 **多种布局**：完整布局(4窗口)、精简布局(2窗口)、监控布局(2窗口)
- 🖥️ **自适应**：自动识别屏幕分辨率并优化布局
- 📺 **Screen管理**：完整的screen会话管理功能
- 🔧 **自定义**：支持自定义窗口配置

### 布局选项
1. 🎯 完整布局 (4窗口) - 推荐
2. 🚀 精简布局 (2窗口) - 仅主要功能
3. 📊 监控布局 (2窗口) - 仅监控

### 使用方法
```bash
# 交互式选择布局
./workspace-layout.sh
```

---

## 9. LAUNCH_GUIDE.md

### 功能描述
启动脚本的详细使用指南文档，包含完整的操作说明、故障排除和最佳实践。

### 主要内容
- 📋 **脚本概览**：所有启动脚本的功能对比
- 🎯 **使用指南**：详细的操作步骤和命令
- 🛠️ **故障排除**：常见问题和解决方案
- 💡 **最佳实践**：会话管理和操作建议

---

## 🚀 启动脚本快速开始

### 推荐使用流程

#### 1. 首次使用
```bash
# 安装完整环境
./setup-all.sh

# 启动工作环境（带说明）
./launch-all.sh
```

#### 2. 日常使用
```bash
# 快速启动（推荐）
./quick-launch.sh
```

#### 3. 自定义布局
```bash
# 选择不同布局
./workspace-layout.sh
```

### 会话管理
```bash
# 查看所有会话
screen -list

# 连接到训练会话
screen -r gensyn
screen -r nexus

# 从会话中分离
Ctrl+A, D
```

---

*最后更新：2024年8月 - 新增启动脚本支持*