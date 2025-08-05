#!/usr/bin/env python3
"""
修复TRL库中reward_model未定义的bug
解决 UnboundLocalError: cannot access local variable 'reward_model' 错误
"""

import os
import sys
import shutil
from pathlib import Path

def fix_trl_grpo_script():
    """修复TRL GRPO脚本中的reward_model bug"""
    
    print("🔧 修复TRL库reward_model bug...")
    
    # 查找TRL安装路径
    try:
        import trl
        trl_path = Path(trl.__file__).parent
        grpo_script = trl_path / "scripts" / "grpo.py"
        
        if not grpo_script.exists():
            print(f"❌ 找不到TRL GRPO脚本: {grpo_script}")
            return False
            
        print(f"📁 找到TRL脚本: {grpo_script}")
        
        # 备份原始文件
        backup_path = grpo_script.with_suffix('.py.backup')
        if not backup_path.exists():
            shutil.copy2(grpo_script, backup_path)
            print(f"💾 已备份原始文件: {backup_path}")
        
        # 读取原始文件
        with open(grpo_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经修复
        if 'reward_model = None' in content:
            print("✅ TRL脚本已经修复")
            return True
        
        # 应用修复
        # 在main函数开始处初始化reward_model
        fixes = [
            # 修复1: 在函数开始处初始化reward_model
            {
                'search': 'def main(script_args, training_args, model_args):',
                'replace': '''def main(script_args, training_args, model_args):
    # Fix: Initialize reward_model to avoid UnboundLocalError
    reward_model = None'''
            },
            # 修复2: 确保reward_funcs参数正确处理
            {
                'search': 'reward_funcs=reward_model,',
                'replace': 'reward_funcs=reward_model if reward_model is not None else script_args.reward_funcs,'
            }
        ]
        
        modified = False
        for fix in fixes:
            if fix['search'] in content:
                content = content.replace(fix['search'], fix['replace'])
                modified = True
                print(f"✅ 应用修复: {fix['search'][:50]}...")
        
        if modified:
            # 写入修复后的文件
            with open(grpo_script, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ TRL脚本修复完成")
            return True
        else:
            print("⚠️  未找到需要修复的代码模式")
            return False
            
    except ImportError:
        print("❌ 未找到TRL库，请确保已安装")
        return False
    except Exception as e:
        print(f"❌ 修复过程出错: {e}")
        return False

def create_alternative_training_script():
    """创建替代的训练脚本，绕过TRL bug"""
    
    script_content = '''#!/usr/bin/env python3
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
'''
    
    script_path = Path("ops/fixes/alternative_train.py")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 添加执行权限
    script_path.chmod(0o755)
    
    print(f"📄 创建替代训练脚本: {script_path}")
    return script_path

def main():
    """主函数"""
    print("🔧 RL-Swarm TRL Bug 修复工具")
    print("=" * 40)
    
    # 方法1: 尝试直接修复TRL库
    print("\n🔨 方法1: 修复TRL库...")
    if fix_trl_grpo_script():
        print("✅ TRL库修复成功!")
        print("\n💡 现在可以重新运行: ./manage.sh")
    else:
        print("⚠️  TRL库修复失败，使用备用方案...")
        
        # 方法2: 创建替代脚本
        print("\n🔨 方法2: 创建替代训练脚本...")
        script_path = create_alternative_training_script()
        print(f"✅ 替代脚本创建成功: {script_path}")
    
    print("\n🎯 修复完成!")
    print("\n📚 使用说明:")
    print("1. 重新启动节点: ./manage.sh")
    print("2. 如果仍有问题，请检查日志: tail -f logs/*.log")
    print("3. 运行诊断: ./ops/scripts/diagnose_node_visibility.sh")

if __name__ == "__main__":
    main() 