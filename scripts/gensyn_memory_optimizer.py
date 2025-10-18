#!/usr/bin/env python3
"""
Gensyn Memory Optimizer - Çalışırken Bellek Temizleme
macOS için özel olarak optimize edilmiş
"""

import os
import sys
import time
import psutil
import subprocess
import threading
from datetime import datetime

class GensynMemoryOptimizer:
    def __init__(self):
        self.running = False
        self.cleanup_interval = 30  # 30 saniyede bir temizlik
        self.memory_threshold = 80  # %80 memory kullanımında temizlik
        
    def get_memory_usage(self):
        """Bellek kullanımını al"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'used': memory.used,
            'free': memory.free,
            'percent': memory.percent,
            'available': memory.available
        }
    
    def get_swap_usage(self):
        """Swap kullanımını al"""
        try:
            result = subprocess.run(['sysctl', 'vm.swapusage'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Parse swap usage
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'vm.swapusage:' in line:
                        parts = line.split()
                        total = float(parts[2].replace('M', ''))
                        used = float(parts[4].replace('M', ''))
                        free = float(parts[6].replace('M', ''))
                        return {
                            'total': total,
                            'used': used,
                            'free': free,
                            'percent': (used / total) * 100
                        }
        except Exception as e:
            print(f"Swap bilgisi alınamadı: {e}")
        return None
    
    def clear_pytorch_cache(self):
        """PyTorch cache'ini temizle"""
        try:
            import torch
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
                print("✅ PyTorch MPS cache temizlendi")
            else:
                print("⚠️ PyTorch MPS mevcut değil")
        except ImportError:
            print("⚠️ PyTorch yüklü değil")
        except Exception as e:
            print(f"❌ PyTorch cache temizlenemedi: {e}")
    
    def clear_python_garbage(self):
        """Python garbage collection"""
        try:
            import gc
            collected = gc.collect()
            print(f"✅ Python garbage collection: {collected} obje temizlendi")
        except Exception as e:
            print(f"❌ Garbage collection hatası: {e}")
    
    def optimize_macos_memory(self):
        """macOS memory optimizasyonu"""
        try:
            # Memory pressure temizle
            subprocess.run(['purge'], check=False)
            print("✅ macOS memory pressure temizlendi")
            
            # Swap ayarlarını optimize et
            subprocess.run(['sudo', 'sysctl', 'vm.swappiness=1'], check=False)
            subprocess.run(['sudo', 'sysctl', 'vm.vfs_cache_pressure=50'], check=False)
            print("✅ macOS swap ayarları optimize edildi")
            
        except Exception as e:
            print(f"⚠️ macOS optimizasyon hatası: {e}")
    
    def cleanup_memory(self):
        """Bellek temizleme işlemi"""
        print(f"\n🧹 [{datetime.now().strftime('%H:%M:%S')}] Bellek temizleme başlatılıyor...")
        
        # PyTorch cache temizle
        self.clear_pytorch_cache()
        
        # Python garbage collection
        self.clear_python_garbage()
        
        # macOS memory optimizasyonu
        self.optimize_macos_memory()
        
        # Bellek durumunu göster
        memory = self.get_memory_usage()
        swap = self.get_swap_usage()
        
        print(f"📊 Bellek Durumu:")
        print(f"   RAM: {memory['used']/1024**3:.1f}GB / {memory['total']/1024**3:.1f}GB ({memory['percent']:.1f}%)")
        if swap:
            print(f"   Swap: {swap['used']:.1f}MB / {swap['total']:.1f}MB ({swap['percent']:.1f}%)")
        
        print("✅ Bellek temizleme tamamlandı\n")
    
    def monitor_memory(self):
        """Bellek izleme ve otomatik temizleme"""
        print("🔍 Gensyn Memory Optimizer başlatıldı")
        print("📊 Bellek izleme aktif - Otomatik temizleme çalışıyor")
        print("⏹️  Durdurmak için Ctrl+C\n")
        
        self.running = True
        last_cleanup = time.time()
        
        try:
            while self.running:
                memory = self.get_memory_usage()
                swap = self.get_swap_usage()
                
                # Bellek kullanımı yüksekse temizle
                if (memory['percent'] > self.memory_threshold or 
                    (swap and swap['percent'] > 70)):
                    
                    self.cleanup_memory()
                    last_cleanup = time.time()
                
                # Periyodik temizleme
                elif time.time() - last_cleanup > self.cleanup_interval:
                    self.cleanup_memory()
                    last_cleanup = time.time()
                
                # Durum göster
                print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] "
                      f"RAM: {memory['percent']:.1f}% | "
                      f"Swap: {swap['percent']:.1f}% | "
                      f"Son temizlik: {int(time.time() - last_cleanup)}s önce")
                
                time.sleep(10)  # 10 saniyede bir kontrol
                
        except KeyboardInterrupt:
            print("\n⏹️  Memory optimizer durduruluyor...")
            self.running = False
    
    def start_optimization(self):
        """Optimizasyonu başlat"""
        self.monitor_memory()

def main():
    print("🚀 Gensyn Memory Optimizer")
    print("=" * 50)
    
    optimizer = GensynMemoryOptimizer()
    optimizer.start_optimization()

if __name__ == "__main__":
    main()
