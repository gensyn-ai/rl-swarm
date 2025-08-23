# 🚀 RL Swarm 启动脚本使用指南

## 📋 脚本概览

本项目提供了多个启动脚本，满足不同的使用需求：

### 🎯 主要启动脚本

| 脚本名称 | 功能描述 | 使用场景 |
|---------|---------|---------|
| `launch-all.sh` | **完整启动脚本** - 带确认和详细说明 | 首次使用或需要了解详情时 |
| `quick-launch.sh` | **快速启动脚本** - 直接启动无确认 | 日常使用的快速启动 |
| `workspace-layout.sh` | **布局管理脚本** - 灵活的窗口布局选择 | 需要自定义布局时 |

### 🔧 辅助脚本

| 脚本名称 | 功能描述 |
|---------|---------|
| `auto-run.sh` | Gensyn 训练监控脚本 |
| `auto-nexus.sh` | Nexus 网络监控脚本 |
| `run_rl_swarm.sh` | Gensyn 训练主程序 |

## 🎯 推荐使用方式

### 1. 日常快速启动（推荐）

```bash
cd ~/rl-swarm  # 或者你的项目实际路径
./quick-launch.sh
```

**功能**：直接启动4个窗口，无需确认
- 窗口1: 🤖 Gensyn 训练会话 (screen)
- 窗口2: 📊 Gensyn 监控会话 (auto-run.sh)
- 窗口3: 🌐 Nexus 运行会话 (screen)
- 窗口4: 📈 Nexus 监控会话 (auto-nexus.sh)

### 2. 完整启动（首次使用）

```bash
cd ~/rl-swarm  # 或者你的项目实际路径
./launch-all.sh
```

**功能**：提供详细说明和确认提示，适合首次使用

### 3. 自定义布局

```bash
cd ~/rl-swarm  # 或者你的项目实际路径
./workspace-layout.sh
```

**功能**：提供多种布局选择，可自定义窗口配置

## 🖥️ 窗口布局说明

启动后的4窗口布局：

```
┌─────────────┬─────────────┐
│ 🤖 Gensyn   │ 📊 Gensyn   │
│    训练     │    监控     │
├─────────────┼─────────────┤
│ 🌐 Nexus    │ 📈 Nexus    │
│   运行      │   监控      │
└─────────────┴─────────────┘
```

### 各窗口功能详解

#### 🤖 窗口1: Gensyn 训练会话
- **功能**: 运行 RL Swarm 训练任务
- **类型**: Screen 会话 (gensyn)
- **操作**: 
  - 在此窗口运行 `./run_rl_swarm.sh` 启动训练
  - 使用 `Ctrl+A, D` 分离会话
  - 使用 `screen -r gensyn` 重新连接

#### 📊 窗口2: Gensyn 监控会话
- **功能**: 自动监控 Gensyn 训练状态
- **脚本**: `auto-run.sh`
- **监控内容**: 
  - 进程状态检查
  - 自动重启机制
  - 连接状态监控
  - 异常检测和处理

#### 🌐 窗口3: Nexus 运行会话
- **功能**: 运行 Nexus 网络节点
- **类型**: Screen 会话 (nexus)
- **操作**:
  - 自动连接现有会话或创建新会话
  - 在会话中运行 Nexus 相关命令
  - 使用 `screen -r nexus` 重新连接

#### 📈 窗口4: Nexus 监控会话
- **功能**: 自动监控 Nexus 节点状态
- **脚本**: `auto-nexus.sh`
- **监控内容**:
  - Nexus 进程状态
  - 自动重启机制
  - 网络连接状态
  - 性能监控

## 📱 操作指南

### 基本操作

```bash
# 给脚本添加执行权限
chmod +x *.sh

# 快速启动完整环境
./quick-launch.sh

# 查看所有 screen 会话
screen -list

# 连接到特定会话
screen -r gensyn    # 连接 Gensyn 训练会话
screen -r nexus     # 连接 Nexus 运行会话
```

### Screen 会话操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 分离会话 | `Ctrl+A, D` | 从会话中分离，保持后台运行 |
| 重新连接 | `screen -r <session_name>` | 重新连接到指定会话 |
| 查看会话 | `screen -list` | 查看所有会话列表 |
| 结束会话 | `screen -X -S <session_name> quit` | 结束指定会话 |

### 窗口管理

| 操作 | 快捷键/命令 | 说明 |
|------|-------------|------|
| 窗口切换 | `Cmd+Tab` | 在应用程序间切换 |
| 重新布局 | `./workspace-layout.sh` | 重新设置窗口布局 |
| 关闭窗口 | `Cmd+W` | 关闭当前终端窗口 |

## 🛠️ 故障排除

### 常见问题

#### 1. 脚本无执行权限
```bash
chmod +x launch-all.sh quick-launch.sh workspace-layout.sh
```

#### 2. Screen 会话冲突
```bash
# 查看现有会话
screen -list

# 清除冲突会话
screen -X -S gensyn quit
screen -X -S nexus quit
```

#### 3. 窗口位置异常
```bash
# 重新运行布局脚本
./workspace-layout.sh
```

#### 4. 监控脚本不工作
检查必要文件是否存在：
```bash
ls -la auto-run.sh auto-nexus.sh run_rl_swarm.sh
```

### 日志文件

| 日志文件 | 内容 | 位置 |
|---------|------|------|
| `auto_monitor.log` | Gensyn 监控日志 | 项目根目录 |
| `nexus_monitor.log` | Nexus 监控日志 | 项目根目录 |
| `logs/swarm_launcher.log` | Gensyn 训练日志 | logs/ 目录 |

## 🎉 使用流程

### 首次启动完整流程

1. **准备环境**
   ```bash
   cd ~/rl-swarm  # 或者你的项目实际路径
   chmod +x *.sh
   ```

2. **启动工作环境**
   ```bash
   ./launch-all.sh
   ```

3. **开始训练**
   - 在🤖 Gensyn 训练窗口中运行：
     ```bash
     ./run_rl_swarm.sh
     ```

4. **监控状态**
   - 📊 Gensyn 监控窗口会自动显示训练状态
   - 📈 Nexus 监控窗口会自动显示网络状态

5. **日常使用**
   - 后续可直接使用 `./quick-launch.sh` 快速启动

### 会话管理最佳实践

1. **保持会话运行**: 使用 `Ctrl+A, D` 分离会话而不是关闭
2. **定期检查**: 通过监控窗口查看运行状态
3. **安全退出**: 先停止训练任务，再退出会话
4. **重新连接**: 使用 `screen -r` 重新连接到会话

## 📞 支持

如有问题，请检查：
1. 确保所有脚本有执行权限
2. 确保 screen 命令已安装
3. 确保项目依赖已正确安装
4. 查看相关日志文件获取详细信息

祝你使用愉快！🚀