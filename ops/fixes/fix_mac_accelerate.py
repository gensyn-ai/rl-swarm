#!/usr/bin/env python3
"""
快速修复Apple Silicon Mac上的accelerate库兼容性问题
这个脚本会monkey patch accelerate库中的问题函数
"""

import os
import sys
from typing import Optional

def patch_accelerate_dataloader():
    """修复accelerate DataLoader在Apple Silicon上的UnboundLocalError问题"""
    try:
        import accelerate.data_loader
        
        # 保存原始方法
        original_iter = accelerate.data_loader.DataLoaderShard.__iter__
        
        def patched_iter(self):
            """修复后的__iter__方法"""
            try:
                return original_iter(self)
            except UnboundLocalError as e:
                if "current_batch" in str(e):
                    print("🔧 检测到Apple Silicon兼容性问题，应用修复...")
                    # 使用更安全的迭代方式
                    for batch in self.dataset:
                        current_batch = batch
                        yield accelerate.utils.send_to_device(
                            current_batch, 
                            self.device, 
                            non_blocking=self._non_blocking
                        )
                else:
                    raise e
        
        # 应用补丁
        accelerate.data_loader.DataLoaderShard.__iter__ = patched_iter
        print("✅ 已应用Apple Silicon兼容性修复")
        
    except ImportError:
        print("⚠️  accelerate库未安装")
    except Exception as e:
        print(f"⚠️  修复失败: {e}")

def apply_mac_optimizations():
    """应用Mac特定的优化设置"""
    # 设置Apple Silicon优化环境变量
    os.environ.update({
        'PYTORCH_ENABLE_MPS_FALLBACK': '1',
        'PYTORCH_MPS_HIGH_WATERMARK_RATIO': '0.0',
        'OMP_NUM_THREADS': '4',  # M4有4个性能核心
        'MKL_NUM_THREADS': '4',
        'TOKENIZERS_PARALLELISM': 'false',  # 避免警告
    })
    
    # 如果可用，启用MPS后端
    try:
        import torch
        if torch.backends.mps.is_available():
            print("🍎 MPS后端可用，将使用GPU加速")
        else:
            print("💾 使用CPU模式")
    except:
        pass

if __name__ == "__main__":
    print("🚀 启动RL-Swarm Apple Silicon兼容性修复...")
    apply_mac_optimizations()
    patch_accelerate_dataloader()
    
    # 导入并运行原始训练脚本
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        print(f"📂 运行训练脚本: {script_path}")
        exec(open(script_path).read())
    else:
        print("✅ 修复已应用，请重新运行训练脚本") 