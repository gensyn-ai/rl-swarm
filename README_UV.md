# RL-Swarm with UV

这个文档说明如何使用 [uv](https://github.com/astral-sh/uv) 来运行 RL-Swarm 项目。

## 什么是 UV？

UV 是一个快速的 Python 包管理器和安装器，用 Rust 编写。它比传统的 pip 和 venv 更快，并且提供了更好的依赖解析。

## 快速开始

### 1. 安装 UV

如果还没有安装 uv，运行以下命令：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

然后重新加载 shell 配置：
```bash
source ~/.bashrc
```

### 2. 运行项目

使用我们提供的脚本：

```bash
./run_rl_swarm_uv.sh
```

或者手动设置：

```bash
# 安装依赖（CPU 模式）
uv sync --no-dev

# 安装依赖（GPU 模式）
uv sync --extra gpu --no-dev
uv pip install flash-attn --no-build-isolation

# 运行训练
uv run python -m hivemind_exp.gsm8k.train_single_gpu [参数]
```

## 项目配置

项目使用 `pyproject.toml` 进行配置，包含：

- **基础依赖**: 所有必需的 Python 包
- **GPU 依赖**: 可选的 GPU 相关包（torch, bitsandbytes, vllm 等）
- **开发依赖**: 测试和开发工具

## 环境变量

可以通过环境变量控制运行模式：

```bash
# CPU 模式
export CPU_ONLY=1

# 设置 Hugging Face token
export HF_TOKEN="your_token_here"

# 其他配置
export PUB_MULTI_ADDRS=""
export PEER_MULTI_ADDRS="/ip4/38.101.215.13/tcp/30002/p2p/QmQ2gEXoPJg6iMBSUFWGzAabS2VhnzuS782Y637hGjfsRJ"
export HOST_MULTI_ADDRS="/ip4/0.0.0.0/tcp/38331"
```

## UV 的优势

1. **更快的安装**: UV 比 pip 快 10-100 倍
2. **更好的依赖解析**: 更智能的依赖冲突解决
3. **原生虚拟环境**: 无需手动创建 venv
4. **锁文件支持**: 确保依赖版本一致性
5. **并行安装**: 同时安装多个包

## 故障排除

### 常见问题

1. **UV 未找到**: 确保正确安装了 uv 并重新加载 shell
2. **GPU 包安装失败**: 尝试先安装 CPU 版本，然后单独安装 GPU 包
3. **权限问题**: 确保脚本有执行权限 `chmod +x run_rl_swarm_uv.sh`

### 调试命令

```bash
# 检查 UV 版本
uv --version

# 查看已安装的包
uv pip list

# 清理缓存
uv cache clean

# 重新同步依赖
uv sync --reinstall
```

## 与原始脚本的区别

- 使用 `uv sync` 替代 `pip install -r requirements.txt`
- 使用 `uv run` 替代直接运行 Python
- 自动检测并安装 uv（如果未安装）
- 更好的错误处理和用户反馈

## 更多信息

- [UV 官方文档](https://docs.astral.sh/uv/)
- [RL-Swarm 项目](https://github.com/gensyn-ai/rl-swarm)
- [Hivemind 文档](https://learning-at-home.readthedocs.io/) 