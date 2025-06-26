# RL-Swarm 自动化运行指南

## 概述

现在 `run_rl_swarm_mac.sh` 脚本支持通过环境变量自动输入，无需手动交互式输入。这样可以方便地进行自动化部署和批量运行。

## 环境变量配置

### 可用的环境变量

| 环境变量 | 说明 | 可选值 | 默认行为 |
|---------|------|-------|---------|
| `AUTO_TESTNET` | 是否连接测试网 | `y`, `n` | 进入交互模式 |
| `AUTO_SWARM` | 选择加入的 swarm | `a` (Math), `b` (Math Hard) | 进入交互模式 |
| `AUTO_HF_HUB` | 是否推送到 Hugging Face Hub | `y`, `n` | 进入交互模式 |
| `HF_TOKEN` | Hugging Face 访问令牌 | 你的令牌字符串 | 进入交互模式 |

### 配置示例

#### 1. 快速启动 (推荐新手)
```bash
# 使用默认配置的快速启动脚本
./ops/scripts/quick_start_rl_swarm.sh
```

#### 2. 自定义环境变量
```bash
# 连接测试网，选择 Math (A) swarm，不推送到 HF Hub
AUTO_TESTNET=y AUTO_SWARM=a AUTO_HF_HUB=n ./ops/scripts/run_rl_swarm_mac.sh

# 本地模式，选择 Math Hard (B) swarm
AUTO_TESTNET=n AUTO_SWARM=b AUTO_HF_HUB=n ./ops/scripts/run_rl_swarm_mac.sh

# 完整配置包含 HF Token
HF_TOKEN=hf_xxxxxxxxxxxx AUTO_TESTNET=y AUTO_SWARM=a AUTO_HF_HUB=y ./ops/scripts/run_rl_swarm_mac.sh
```

#### 3. 使用 .env 文件
创建 `.env` 文件：
```bash
# .env
AUTO_TESTNET=y
AUTO_SWARM=a
AUTO_HF_HUB=n
# HF_TOKEN=hf_xxxxxxxxxxxx  # 如果需要推送到 HF Hub
```

然后运行：
```bash
source .env && ./ops/scripts/run_rl_swarm_mac.sh
```

## 使用场景

### 1. 开发测试
```bash
# 快速测试连接 - 本地模式
AUTO_TESTNET=n AUTO_SWARM=a AUTO_HF_HUB=n ./ops/scripts/run_rl_swarm_mac.sh
```

### 2. 生产部署
```bash
# 生产环境 - 连接测试网
AUTO_TESTNET=y AUTO_SWARM=a AUTO_HF_HUB=n ./ops/scripts/run_rl_swarm_mac.sh
```

### 3. 研究实验
```bash
# 使用 Math Hard swarm 进行高难度训练
AUTO_TESTNET=y AUTO_SWARM=b AUTO_HF_HUB=n ./ops/scripts/run_rl_swarm_mac.sh
```

### 4. 模型发布
```bash
# 训练并推送模型到 Hugging Face Hub
HF_TOKEN=your_token_here AUTO_TESTNET=y AUTO_SWARM=a AUTO_HF_HUB=y ./ops/scripts/run_rl_swarm_mac.sh
```

## 脚本选项

### 1. 快速启动脚本
- **路径**: `./ops/scripts/quick_start_rl_swarm.sh`
- **用途**: 新手友好，使用最佳默认配置
- **配置**: 自动连接测试网，选择 Math (A) swarm，不推送到 HF Hub

### 2. 原始脚本（增强版）
- **路径**: `./ops/scripts/run_rl_swarm_mac.sh`
- **用途**: 完全可控，支持所有配置选项
- **配置**: 通过环境变量或交互式输入

### 3. Expect 脚本（备选方案）
- **路径**: `./ops/scripts/auto_run_rl_swarm_mac.exp`
- **用途**: 如果环境变量方法不工作，可以使用 expect 自动化

## 故障排除

### 1. 环境变量不生效
- 确保变量名拼写正确
- 检查变量值是否有效 (`y`, `n`, `a`, `b`)
- 尝试使用 `export` 命令设置变量

### 2. 仍然提示交互输入
- 检查环境变量是否正确设置：`echo $AUTO_TESTNET`
- 确保变量值符合预期格式
- 查看脚本输出的自动配置确认信息

### 3. HF Token 问题
- 确保 `HF_TOKEN` 环境变量已设置
- 验证 token 格式正确（以 `hf_` 开头）
- 如果 `AUTO_HF_HUB=y` 但没有设置 `HF_TOKEN`，脚本会报错

## 安全建议

1. **不要在命令历史中暴露 HF Token**：
   ```bash
   # 不推荐
   HF_TOKEN=hf_secret123 ./script.sh
   
   # 推荐 - 使用 .env 文件
   echo "HF_TOKEN=hf_secret123" > .env
   source .env && ./script.sh
   ```

2. **使用 .gitignore 排除敏感文件**：
   ```
   .env
   *.env
   ```

## 监控和日志

- 自动配置的选择会在控制台显示 🤖 标识
- 所有日志保存在 `$ROOT/logs/` 目录
- 使用 `tail -f logs/performance.log` 监控性能

## 示例工作流

### 完整的自动化工作流程：
```bash
#!/bin/bash
# auto_deploy.sh

# 设置配置
export AUTO_TESTNET=y
export AUTO_SWARM=a  
export AUTO_HF_HUB=n

# 清理之前的运行
rm -rf logs/* 2>/dev/null || true

# 启动训练
echo "🚀 开始自动化 RL-Swarm 训练..."
./ops/scripts/run_rl_swarm_mac.sh

# 训练完成后的处理
echo "✅ 训练完成，检查日志..."
ls -la logs/
```

运行：
```bash
chmod +x auto_deploy.sh
./auto_deploy.sh 