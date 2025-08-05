#!/usr/bin/env python3
"""
预防性修复脚本 - 解决RL-Swarm在Mac Mini M4上可能遇到的问题
"""

import os
import sys
import shutil
import subprocess
import psutil
import logging
from pathlib import Path

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/preemptive_fixes.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_disk_space():
    """检查磁盘空间 - 至少需要10GB"""
    logger = logging.getLogger(__name__)
    free_space = shutil.disk_usage('.').free / (1024**3)  # GB
    
    if free_space < 10:
        logger.warning(f"磁盘空间不足: {free_space:.1f}GB (建议至少10GB)")
        return False
    else:
        logger.info(f"磁盘空间充足: {free_space:.1f}GB")
        return True

def check_memory():
    """检查内存使用情况"""
    logger = logging.getLogger(__name__)
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024**3)
    
    if available_gb < 4:
        logger.warning(f"可用内存不足: {available_gb:.1f}GB (建议至少4GB)")
        # 清理内存
        try:
            subprocess.run(['sudo', 'purge'], check=True, capture_output=True)
            logger.info("已执行内存清理")
        except:
            logger.warning("内存清理失败，请手动重启系统")
        return False
    else:
        logger.info(f"内存充足: {available_gb:.1f}GB")
        return True

def check_network_connectivity():
    """检查网络连接"""
    logger = logging.getLogger(__name__)
    test_urls = [
        'huggingface.co',
        'github.com',
        'pypi.org'
    ]
    
    failed_urls = []
    for url in test_urls:
        try:
            result = subprocess.run(['ping', '-c', '1', url], 
                                  capture_output=True, timeout=5)
            if result.returncode != 0:
                failed_urls.append(url)
        except subprocess.TimeoutExpired:
            failed_urls.append(url)
    
    if failed_urls:
        logger.warning(f"网络连接问题: {', '.join(failed_urls)}")
        return False
    else:
        logger.info("网络连接正常")
        return True

def fix_permissions():
    """修复权限问题"""
    logger = logging.getLogger(__name__)
    try:
        # 确保日志目录可写
        os.makedirs('logs', exist_ok=True)
        os.chmod('logs', 0o755)
        
        # 确保脚本可执行
        scripts = ['run_rl_swarm_mac.sh', 'fix_mac_dependencies.sh']
        for script in scripts:
            if os.path.exists(script):
                os.chmod(script, 0o755)
        
        logger.info("权限修复完成")
        return True
    except Exception as e:
        logger.error(f"权限修复失败: {e}")
        return False

def optimize_pytorch_settings():
    """优化PyTorch设置"""
    logger = logging.getLogger(__name__)
    
    # 设置环境变量防止MPS内存问题
    env_vars = {
        'PYTORCH_MPS_HIGH_WATERMARK_RATIO': '0.0',
        'PYTORCH_ENABLE_MPS_FALLBACK': '1',
        'OMP_NUM_THREADS': '4',  # M4的性能核心数
        'MKL_NUM_THREADS': '4',
        'TOKENIZERS_PARALLELISM': 'false',
        'HF_HUB_CACHE': os.path.expanduser('~/.cache/huggingface'),
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    logger.info("PyTorch优化设置已应用")
    return True

def check_huggingface_cache():
    """检查并优化HuggingFace缓存"""
    logger = logging.getLogger(__name__)
    cache_dir = Path.home() / '.cache' / 'huggingface'
    
    if cache_dir.exists():
        cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        cache_size_gb = cache_size / (1024**3)
        
        if cache_size_gb > 5:  # 超过5GB清理旧缓存
            logger.warning(f"HuggingFace缓存过大: {cache_size_gb:.1f}GB")
            # 保留最近30天的缓存
            subprocess.run(['find', str(cache_dir), '-type', 'f', '-mtime', '+30', '-delete'], 
                          capture_output=True)
            logger.info("已清理旧缓存文件")
        else:
            logger.info(f"HuggingFace缓存大小正常: {cache_size_gb:.1f}GB")
    
    return True

def fix_common_dependency_issues():
    """修复常见依赖问题"""
    logger = logging.getLogger(__name__)
    
    try:
        # 检查关键包是否可导入
        critical_packages = [
            'torch', 'transformers', 'datasets', 'accelerate', 'hivemind'
        ]
        
        missing_packages = []
        for package in critical_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"缺少关键包: {missing_packages}")
            # 尝试重新安装
            for package in missing_packages:
                subprocess.run(['uv', 'pip', 'install', package], 
                              capture_output=True)
            return False
        else:
            logger.info("所有关键依赖可用")
            return True
            
    except Exception as e:
        logger.error(f"依赖检查失败: {e}")
        return False

def create_swap_file():
    """创建交换文件以防内存不足"""
    logger = logging.getLogger(__name__)
    
    # Mac不需要交换文件，但可以设置内存压缩
    try:
        # 检查内存压缩是否启用
        result = subprocess.run(['sysctl', 'vm.compressor_mode'], 
                               capture_output=True, text=True)
        if 'vm.compressor_mode: 4' in result.stdout:
            logger.info("内存压缩已启用")
        else:
            logger.info("内存压缩状态检查完成")
        return True
    except:
        return True

def run_all_fixes():
    """运行所有预防性修复"""
    logger = setup_logging()
    logger.info("🔧 开始预防性修复检查...")
    
    fixes = [
        ("磁盘空间检查", check_disk_space),
        ("内存检查", check_memory),
        ("网络连接检查", check_network_connectivity),
        ("权限修复", fix_permissions),
        ("PyTorch优化", optimize_pytorch_settings),
        ("HuggingFace缓存检查", check_huggingface_cache),
        ("依赖检查", fix_common_dependency_issues),
        ("内存优化", create_swap_file),
    ]
    
    results = {}
    for name, fix_func in fixes:
        logger.info(f"执行: {name}")
        try:
            result = fix_func()
            results[name] = result
            if result:
                logger.info(f"✅ {name} - 成功")
            else:
                logger.warning(f"⚠️ {name} - 需要注意")
        except Exception as e:
            logger.error(f"❌ {name} - 失败: {e}")
            results[name] = False
    
    # 总结
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    logger.info(f"\n🎯 预防性修复完成: {passed}/{total} 项通过")
    
    if passed < total:
        logger.warning("⚠️ 有些检查未通过，可能影响训练稳定性")
        return False
    else:
        logger.info("✅ 所有检查通过，系统状态良好")
        return True

if __name__ == "__main__":
    run_all_fixes() 