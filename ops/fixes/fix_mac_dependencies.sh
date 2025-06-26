#!/bin/bash

# 修复Mac依赖问题的完整解决方案
# 解决Apple Silicon上的accelerate兼容性问题

echo "🔧 修复Apple Silicon上的依赖兼容性问题..."

cd /Users/mac/work/gensyn/rl-swarm

# 1. 安装兼容的accelerate版本
echo "📦 安装兼容的accelerate版本..."
uv pip install "accelerate==1.1.1" --force-reinstall --quiet

# 2. 确保torch版本兼容
echo "🔥 检查torch版本兼容性..."
uv pip install torch --index-url https://download.pytorch.org/whl/cpu --force-reinstall --quiet

# 3. 安装缺失的grpcio-tools
echo "🛠️ 安装grpcio-tools..."
uv pip install grpcio-tools --quiet

# 4. 验证关键库
echo "✅ 验证安装..."
uv run python -c "
import accelerate
import torch
import transformers
print('✅ accelerate:', accelerate.__version__)
print('✅ torch:', torch.__version__)  
print('✅ transformers:', transformers.__version__)
print('🍎 Apple Silicon兼容性修复完成!')
"

echo "🎉 依赖修复完成! 现在可以重新运行训练了。" 