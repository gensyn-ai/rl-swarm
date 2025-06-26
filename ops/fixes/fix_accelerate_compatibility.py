#!/usr/bin/env python3
"""
Fix accelerate compatibility issues on Apple Silicon M4
解决 Apple Silicon M4 上的 accelerate 兼容性问题
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """执行命令并处理错误"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e.stderr}")
        return False

def check_environment():
    """检查当前环境"""
    print("🔍 检查当前环境...")
    
    # 检查是否在虚拟环境中
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ 请先激活虚拟环境: source .venv/bin/activate")
        return False
    
    print("✅ 虚拟环境已激活")
    return True

def fix_accelerate_versions():
    """修复 accelerate 版本兼容性问题"""
    print("\n🔧 修复 accelerate 兼容性问题...")
    
    # 方案1: 降级到稳定版本组合
    fixes = [
        {
            "name": "降级 accelerate 到 1.7.0（推荐）",
            "commands": [
                "uv pip install accelerate==1.7.0 --force-reinstall",
            ]
        },
        {
            "name": "使用兼容的torch版本组合",
            "commands": [
                "uv pip install torch==2.4.1 --force-reinstall",
                "uv pip install accelerate==1.7.0 --force-reinstall",
            ]
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"\n选项 {i}: {fix['name']}")
        choice = input(f"是否执行此修复？(y/n): ").lower()
        
        if choice == 'y':
            all_success = True
            for cmd in fix['commands']:
                if not run_command(cmd, f"执行: {cmd}"):
                    all_success = False
                    break
            
            if all_success:
                print(f"✅ {fix['name']} 修复完成")
                return True
            else:
                print(f"❌ {fix['name']} 修复失败，尝试下一个方案...")
                continue
    
    return False

def patch_accelerate_dataloader():
    """为 accelerate data_loader.py 应用补丁"""
    print("\n🔧 查找并修补 accelerate data_loader.py...")
    
    # 查找 accelerate 安装位置
    try:
        result = subprocess.run(['python', '-c', 'import accelerate; print(accelerate.__file__)'], 
                              capture_output=True, text=True, check=True)
        accelerate_path = Path(result.stdout.strip()).parent
        dataloader_path = accelerate_path / "data_loader.py"
        
        if not dataloader_path.exists():
            print(f"❌ 找不到 data_loader.py: {dataloader_path}")
            return False
        
        print(f"📍 找到 accelerate data_loader.py: {dataloader_path}")
        
        # 备份原文件
        backup_path = dataloader_path.with_suffix('.py.backup')
        if not backup_path.exists():
            import shutil
            shutil.copy2(dataloader_path, backup_path)
            print(f"📦 已备份原文件到: {backup_path}")
        
        # 读取原文件内容
        with open(dataloader_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 应用补丁：在 __iter__ 方法中初始化 current_batch
        if 'current_batch = None' not in content:
            # 查找 __iter__ 方法的开始
            lines = content.split('\n')
            patched_lines = []
            in_iter_method = False
            patch_applied = False
            
            for line in lines:
                if 'def __iter__(self):' in line:
                    in_iter_method = True
                    patched_lines.append(line)
                    # 添加 current_batch 初始化
                    patched_lines.append('        current_batch = None  # Fix for Apple Silicon compatibility')
                    patch_applied = True
                else:
                    patched_lines.append(line)
            
            if patch_applied:
                # 写回修补后的内容
                with open(dataloader_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(patched_lines))
                print("✅ 已应用 data_loader.py 补丁")
                return True
            else:
                print("❌ 未找到需要修补的 __iter__ 方法")
                return False
        else:
            print("✅ 补丁已存在，无需重复应用")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 查找 accelerate 路径失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 应用补丁失败: {e}")
        return False

def verify_fix():
    """验证修复是否成功"""
    print("\n🔍 验证修复结果...")
    
    # 检查版本
    run_command("uv pip list | grep -E 'accelerate|torch|transformers'", "检查软件包版本")
    
    # 测试导入
    test_script = '''
import torch
import accelerate
import transformers
print("✅ 所有软件包导入成功")
print(f"torch: {torch.__version__}")
print(f"accelerate: {accelerate.__version__}")
print(f"transformers: {transformers.__version__}")
'''
    
    try:
        result = subprocess.run(['python', '-c', test_script], 
                              capture_output=True, text=True, check=True)
        print("✅ 软件包导入测试通过")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 软件包导入测试失败: {e.stderr}")
        return False

def main():
    """主函数"""
    print("🍎 Apple Silicon M4 - Accelerate 兼容性修复工具")
    print("=" * 50)
    
    if not check_environment():
        sys.exit(1)
    
    print("\n当前问题: UnboundLocalError in accelerate data_loader.py")
    print("解决方案选择：")
    print("1. 降级软件包版本（推荐）")
    print("2. 应用代码补丁")
    
    choice = input("\n请选择修复方案 (1/2): ").strip()
    
    if choice == "1":
        if fix_accelerate_versions():
            print("\n🎉 版本修复完成！")
        else:
            print("\n❌ 版本修复失败，尝试方案2...")
            choice = "2"
    
    if choice == "2":
        if patch_accelerate_dataloader():
            print("\n🎉 补丁修复完成！")
        else:
            print("\n❌ 补丁修复失败")
            sys.exit(1)
    
    # 验证修复
    if verify_fix():
        print("\n🎉 修复验证成功！现在可以重新启动 RL-Swarm")
        print("\n重启命令: ./manage.sh")
    else:
        print("\n❌ 修复验证失败，可能需要手动检查")

if __name__ == "__main__":
    main() 