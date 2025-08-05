#!/usr/bin/env python3
"""
RL-Swarm 训练脚本 - 绕过TRL reward_model bug
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_training_with_fixed_args():
    """使用修复后的参数运行训练"""
    
    # 导入必要的模块
    try:
        from hivemind_exp.gsm8k.train_single_gpu import main as train_main
        from hivemind_exp.runner.gensyn.testnet_grpo_runner import TestnetGRPORunner
        from hivemind_exp.chain_utils import setup_web3, ModalSwarmCoordinator
        import argparse
        
        # 解析命令行参数
        parser = argparse.ArgumentParser()
        parser.add_argument("--config", required=True, help="Config file path")
        parser.add_argument("--modal_org_id", help="Modal organization ID")
        parser.add_argument("--contract_address", help="Contract address")
        parser.add_argument("--identity_path", default="swarm.pem", help="Identity file path")
        parser.add_argument("--game", default="gsm8k", help="Game/dataset name")
        
        args = parser.parse_args()
        
        # 设置环境变量避免reward_model错误
        os.environ['REWARD_FUNCS'] = 'think_format_reward'
        
        print("🚀 启动RL-Swarm训练 (使用修复版本)...")
        print(f"📝 配置文件: {args.config}")
        print(f"🔑 ORG ID: {args.modal_org_id}")
        print(f"📊 数据集: {args.game}")
        
        # 调用原始训练函数
        train_main()
        
    except Exception as e:
        print(f"❌ 训练启动失败: {e}")
        print("💡 建议:")
        print("1. 检查TRL库是否正确安装")
        print("2. 运行修复脚本: python ops/fixes/fix_trl_reward_model_bug.py")
        print("3. 重新启动训练: ./manage.sh")
        sys.exit(1)

if __name__ == "__main__":
    run_training_with_fixed_args()
