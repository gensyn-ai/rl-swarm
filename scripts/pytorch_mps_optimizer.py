#!/usr/bin/env python3

"""
PyTorch MPS Optimizer for RL-Swarm on macOS
This script optimizes PyTorch MPS settings to prevent OOM issues
"""

import os
import sys
import gc
import torch
import psutil
import time
from typing import Optional, Dict, Any

class PyTorchMPSOptimizer:
    """Optimizes PyTorch MPS settings for macOS to prevent OOM issues"""
    
    def __init__(self):
        self.original_settings = {}
        self.optimized_settings = {
            'PYTORCH_MPS_HIGH_WATERMARK_RATIO': '0.0',
            'PYTORCH_MPS_ALLOCATOR_POLICY': 'expandable_segments',
            'MPS_DEVICE_MEMORY_LIMIT': '0.8',
            'OMP_NUM_THREADS': '4',
            'MKL_NUM_THREADS': '4',
            'NUMEXPR_NUM_THREADS': '4'
        }
    
    def setup_environment(self) -> None:
        """Set up optimized environment variables"""
        print("🔧 Setting up optimized PyTorch MPS environment...")
        
        for key, value in self.optimized_settings.items():
            self.original_settings[key] = os.environ.get(key)
            os.environ[key] = value
            print(f"  {key} = {value}")
        
        print("✅ Environment variables set")
    
    def check_mps_availability(self) -> bool:
        """Check if MPS is available and working"""
        if not torch.backends.mps.is_available():
            print("❌ MPS is not available on this system")
            return False
        
        if not torch.backends.mps.is_built():
            print("❌ MPS is not built with this PyTorch version")
            return False
        
        print("✅ MPS is available and built")
        return True
    
    def optimize_mps_settings(self) -> None:
        """Optimize MPS settings for memory management"""
        if not self.check_mps_availability():
            return
        
        print("⚙️ Optimizing MPS settings...")
        
        # Set memory management settings
        if hasattr(torch.backends.mps, 'set_per_process_memory_fraction'):
            torch.backends.mps.set_per_process_memory_fraction(0.8)
            print("  Set MPS memory fraction to 0.8")
        
        # Enable memory management
        if hasattr(torch.backends.mps, 'set_memory_management'):
            torch.backends.mps.set_memory_management(True)
            print("  Enabled MPS memory management")
        
        print("✅ MPS settings optimized")
    
    def clear_mps_cache(self) -> None:
        """Clear MPS cache to free memory"""
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
            print("🧹 MPS cache cleared")
    
    def force_garbage_collection(self) -> None:
        """Force Python garbage collection"""
        collected = gc.collect()
        print(f"🧹 Garbage collection: {collected} objects collected")
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory information"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total_memory': memory.total,
            'available_memory': memory.available,
            'used_memory': memory.used,
            'memory_percent': memory.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent
        }
    
    def print_memory_status(self) -> None:
        """Print current memory status"""
        info = self.get_memory_info()
        
        print("📊 Memory Status:")
        print(f"  Total Memory: {info['total_memory'] / (1024**3):.2f} GB")
        print(f"  Available Memory: {info['available_memory'] / (1024**3):.2f} GB")
        print(f"  Used Memory: {info['used_memory'] / (1024**3):.2f} GB ({info['memory_percent']:.1f}%)")
        print(f"  Swap Total: {info['swap_total'] / (1024**3):.2f} GB")
        print(f"  Swap Used: {info['swap_used'] / (1024**3):.2f} GB ({info['swap_percent']:.1f}%)")
    
    def monitor_memory(self, interval: int = 10) -> None:
        """Monitor memory usage continuously"""
        print(f"📊 Monitoring memory every {interval} seconds...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.print_memory_status()
                print("-" * 50)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Memory monitoring stopped")
    
    def optimize_for_training(self) -> None:
        """Optimize settings specifically for RL training"""
        print("🎯 Optimizing for RL training...")
        
        # Set training-specific optimizations
        os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
        os.environ['PYTORCH_MPS_ALLOCATOR_POLICY'] = 'expandable_segments'
        os.environ['MPS_DEVICE_MEMORY_LIMIT'] = '0.8'
        
        # Set thread limits for better performance
        os.environ['OMP_NUM_THREADS'] = '4'
        os.environ['MKL_NUM_THREADS'] = '4'
        os.environ['NUMEXPR_NUM_THREADS'] = '4'
        
        # Clear caches
        self.clear_mps_cache()
        self.force_garbage_collection()
        
        print("✅ Training optimizations applied")
    
    def create_memory_script(self) -> None:
        """Create a memory management script"""
        script_content = '''#!/usr/bin/env bash

# Auto-generated memory management script for RL-Swarm
# This script optimizes memory settings for macOS

# PyTorch MPS optimizations
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_MPS_ALLOCATOR_POLICY=expandable_segments
export MPS_DEVICE_MEMORY_LIMIT=0.8

# Thread optimizations
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export NUMEXPR_NUM_THREADS=4

# Memory management
export MALLOC_TRIM_THRESHOLD_=131072
export MALLOC_MMAP_THRESHOLD_=131072
export MALLOC_MMAP_MAX_=65536

# Clear memory before starting
sudo purge 2>/dev/null || true

echo "Memory optimization environment loaded"
echo "Starting RL-Swarm with optimized settings..."
'''
        
        with open('memory_optimize.sh', 'w') as f:
            f.write(script_content)
        
        os.chmod('memory_optimize.sh', 0o755)
        print("✅ Memory optimization script created: memory_optimize.sh")
    
    def restore_original_settings(self) -> None:
        """Restore original environment settings"""
        print("🔄 Restoring original settings...")
        
        for key, value in self.original_settings.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        print("✅ Original settings restored")

def main():
    """Main function"""
    optimizer = PyTorchMPSOptimizer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            optimizer.setup_environment()
            optimizer.optimize_mps_settings()
        elif command == "clear":
            optimizer.clear_mps_cache()
            optimizer.force_garbage_collection()
        elif command == "status":
            optimizer.print_memory_status()
        elif command == "monitor":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            optimizer.monitor_memory(interval)
        elif command == "optimize":
            optimizer.optimize_for_training()
        elif command == "create":
            optimizer.create_memory_script()
        else:
            print("Unknown command. Available commands: setup, clear, status, monitor, optimize, create")
    else:
        # Interactive mode
        print("=== PyTorch MPS Optimizer ===")
        print("1. Setup optimized environment")
        print("2. Clear MPS cache")
        print("3. Show memory status")
        print("4. Monitor memory")
        print("5. Optimize for training")
        print("6. Create memory script")
        print("7. Exit")
        
        choice = input("Choose an option (1-7): ")
        
        if choice == "1":
            optimizer.setup_environment()
            optimizer.optimize_mps_settings()
        elif choice == "2":
            optimizer.clear_mps_cache()
            optimizer.force_garbage_collection()
        elif choice == "3":
            optimizer.print_memory_status()
        elif choice == "4":
            interval = int(input("Enter monitoring interval in seconds (default 10): ") or "10")
            optimizer.monitor_memory(interval)
        elif choice == "5":
            optimizer.optimize_for_training()
        elif choice == "6":
            optimizer.create_memory_script()
        elif choice == "7":
            sys.exit(0)
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
