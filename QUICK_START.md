# RL-Swarm 快速开始指南

这个项目现在完全支持使用 UV 进行快速部署和运行。

## 🚀 一键启动

### 本地测试模式（推荐新手）
```bash
./run_rl_swarm_local.sh
```
- ✅ 无需网络连接
- ✅ 使用 CPU 模式，资源需求低
- ✅ 快速验证安装是否正确

### 完整 Testnet 模式
```bash
./run_rl_swarm_uv.sh
```
- 🌐 连接到 Gensyn testnet
- 💰 可以赚取奖励
- 🤝 参与分布式训练

## 📋 系统要求

### 基础要求
- Linux/WSL2 环境
- Python 3.9+
- 8GB+ RAM（本地模式）
- 16GB+ RAM（GPU 模式）

### 可选要求
- NVIDIA GPU（用于 GPU 模式）
- Node.js 14+（自动安装）
- Hugging Face Token（可选）

## 🛠 手动安装

如果自动脚本有问题，可以手动安装：

```bash
# 1. 安装 UV
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# 2. 安装依赖
uv sync --no-dev                    # CPU 模式
uv sync --extra gpu --no-dev        # GPU 模式

# 3. 运行训练
uv run python -m hivemind_exp.gsm8k.train_single_gpu \
    --config hivemind_exp/configs/mac/grpo-qwen-2.5-0.5b-local.yaml \
    --game gsm8k
```

## 🔧 故障排除

### Node.js 版本问题
如果遇到 "Expected version >=14" 错误：
```bash
# 手动安装 Node.js 18
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 18 && nvm use 18
```

### P2P 连接问题
如果遇到 "failed to connect to bootstrap peers"：
```bash
# 使用本地模式
./run_rl_swarm_local.sh
```

### 模型下载问题
如果遇到 401 认证错误：
```bash
# 设置 Hugging Face token
export HF_TOKEN="your_token_here"
```

### UV 未找到
```bash
# 重新安装 UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

## 📊 性能对比

| 方法 | 安装时间 | 内存使用 | 兼容性 |
|------|----------|----------|--------|
| pip | 5-15 分钟 | 高 | 中等 |
| UV | 30-90 秒 | 低 | 高 |

## 🎯 下一步

1. **成功运行本地模式** → 尝试 testnet 模式
2. **获得 Hugging Face token** → 上传训练的模型
3. **连接 GPU** → 训练更大的模型
4. **加入社区** → 参与分布式训练

## 🔗 相关链接

- [UV 官方文档](https://docs.astral.sh/uv/)
- [Gensyn 官网](https://www.gensyn.ai/)
- [Hivemind 文档](https://learning-at-home.readthedocs.io/)
- [项目 GitHub](https://github.com/gensyn-ai/rl-swarm)

## 💡 提示

- 首次运行会下载模型，需要良好的网络连接
- 本地模式适合学习和测试
- Testnet 模式可以获得真实的奖励
- 使用 GPU 可以训练更大、更强的模型 