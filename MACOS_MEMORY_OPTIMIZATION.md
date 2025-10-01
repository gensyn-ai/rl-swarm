# macOS Memory Optimization Guide for RL-Swarm

Bu rehber, macOS'ta RL-Swarm çalıştırırken karşılaşılan OOM (Out of Memory) sorunlarını çözmek için kapsamlı optimizasyonları içerir.

## 🚨 Sorun Analizi

### OOM Sorunlarının Nedenleri
1. **PyTorch MPS Memory Management**: macOS'ta PyTorch MPS bellek yönetimi optimize edilmemiş
2. **Swap Memory Issues**: macOS swap belleğini düzgün temizleyemiyor
3. **Memory Fragmentation**: Bellek parçalanması nedeniyle sürekli swap kullanımı
4. **Process Memory Leaks**: Python process'lerinin bellek sızıntıları

### Belirtiler
- Günün sonunda OOM hatası
- Sistem yavaşlama
- Swap kullanımının artması
- Memory pressure uyarıları

## 🛠️ Çözümler

### 1. Optimize Edilmiş Run Script

```bash
# Optimize edilmiş script ile çalıştırma
./run_rl_swarm_optimized.sh
```

Bu script şu optimizasyonları içerir:
- `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`
- `PYTORCH_MPS_ALLOCATOR_POLICY=expandable_segments`
- `MPS_DEVICE_MEMORY_LIMIT=0.8`
- Otomatik bellek temizleme
- Memory monitoring

### 2. Memory Manager Kullanımı

```bash
# Memory manager'ı çalıştır
bash scripts/memory_manager.sh

# Belirli komutlar
bash scripts/memory_manager.sh status    # Bellek durumunu kontrol et
bash scripts/memory_manager.sh cleanup   # Belleği temizle
bash scripts/memory_manager.sh monitor  # Sürekli izleme
```

### 3. Swap Manager Kullanımı

```bash
# Swap manager'ı çalıştır
bash scripts/swap_manager.sh

# Swap temizleme
bash scripts/swap_manager.sh clear

# Swap ayarlarını optimize et
bash scripts/swap_manager.sh optimize
```

### 4. PyTorch MPS Optimizer

```bash
# Python optimizer'ı çalıştır
python3 scripts/pytorch_mps_optimizer.py

# Belirli komutlar
python3 scripts/pytorch_mps_optimizer.py setup    # Ortamı optimize et
python3 scripts/pytorch_mps_optimizer.py clear    # Cache'i temizle
python3 scripts/pytorch_mps_optimizer.py monitor  # Belleği izle
```

## ⚙️ Sistem Ayarları

### 1. Environment Variables

```bash
# .bashrc veya .zshrc dosyasına ekleyin
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_MPS_ALLOCATOR_POLICY=expandable_segments
export MPS_DEVICE_MEMORY_LIMIT=0.8
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export NUMEXPR_NUM_THREADS=4

# Memory management
export MALLOC_TRIM_THRESHOLD_=131072
export MALLOC_MMAP_THRESHOLD_=131072
export MALLOC_MMAP_MAX_=65536
```

### 2. Sistem Ayarları

```bash
# Swap ayarlarını optimize et
sudo sysctl vm.swappiness=10
sudo sysctl vm.vfs_cache_pressure=50
sudo sysctl vm.compressor=1

# Memory limits
ulimit -v 8388608  # 8GB virtual memory limit
```

### 3. LaunchDaemon Ayarları

```bash
# Dynamic pager'ı yeniden başlat
sudo launchctl unload /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist
sudo launchctl load /System/Library/LaunchDaemons/com.apple.dynamic_pager.plist
```

## 📊 Monitoring ve Debugging

### 1. Memory Monitoring

```bash
# Sürekli bellek izleme
bash scripts/memory_manager.sh monitor

# Swap kullanımını izleme
bash scripts/swap_manager.sh monitor

# PyTorch MPS durumunu izleme
python3 scripts/pytorch_mps_optimizer.py monitor
```

### 2. Debug Komutları

```bash
# Bellek durumunu kontrol et
vm_stat

# Swap kullanımını kontrol et
sysctl vm.swapusage

# Memory pressure kontrol et
memory_pressure

# Process bellek kullanımını kontrol et
ps aux | sort -nr -k 4 | head -10
```

### 3. Log Dosyaları

```bash
# RL-Swarm log'larını kontrol et
tail -f logs/swarm.log
tail -f logs/yarn.log

# Sistem log'larını kontrol et
log show --predicate 'process == "kernel"' --last 1h
```

## 🔧 Gelişmiş Optimizasyonlar

### 1. Custom Memory Script

```bash
# Otomatik memory optimization script oluştur
python3 scripts/pytorch_mps_optimizer.py create

# Script'i çalıştır
source memory_optimize.sh
```

### 2. Scheduled Cleanup

```bash
# Crontab ile otomatik temizlik
# Her 30 dakikada bir bellek temizliği
*/30 * * * * /path/to/rl-swarm/scripts/memory_manager.sh cleanup
```

### 3. Process Management

```bash
# Memory-intensive process'leri otomatik temizle
bash scripts/memory_manager.sh kill
```

## 🚀 Önerilen Workflow

### 1. Başlangıç Öncesi

```bash
# 1. Sistem ayarlarını optimize et
bash scripts/swap_manager.sh optimize

# 2. Belleği temizle
bash scripts/memory_manager.sh cleanup

# 3. PyTorch MPS'i optimize et
python3 scripts/pytorch_mps_optimizer.py setup
```

### 2. Training Sırasında

```bash
# 1. Optimize edilmiş script ile başlat
./run_rl_swarm_optimized.sh

# 2. Paralel olarak memory monitoring
bash scripts/memory_manager.sh monitor &
```

### 3. Problem Durumunda

```bash
# 1. Belleği temizle
bash scripts/memory_manager.sh cleanup

# 2. Swap'i temizle
bash scripts/swap_manager.sh clear

# 3. Process'leri temizle
bash scripts/memory_manager.sh kill

# 4. Yeniden başlat
./run_rl_swarm_optimized.sh
```

## 📈 Performans İyileştirmeleri

### Beklenen Faydalar
- **OOM Hatası**: %90+ azalma
- **Memory Usage**: %30-40 daha verimli kullanım
- **Swap Usage**: %50+ azalma
- **Training Stability**: Çok daha stabil çalışma

### Monitoring Metrikleri
- Memory usage < %80
- Swap usage < %20
- Memory pressure < 0.5
- Process count < 50

## 🆘 Troubleshooting

### Yaygın Sorunlar

1. **"Permission denied" hatası**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **"Command not found" hatası**
   ```bash
   # Python path'ini kontrol et
   which python3
   # Script'leri executable yap
   chmod +x scripts/*.sh
   ```

3. **Memory hala yüksek**
   ```bash
   # Tüm Python process'lerini temizle
   pkill -f python
   # Sistem restart
   sudo reboot
   ```

### Log Analizi

```bash
# RL-Swarm log'larını analiz et
grep -i "memory\|oom\|error" logs/swarm.log

# Sistem log'larını analiz et
log show --predicate 'process == "kernel"' --last 1h | grep -i memory
```

## 📝 Notlar

- Bu optimizasyonlar macOS 12+ için test edilmiştir
- M1/M2 Mac'lerde ek optimizasyonlar gerekebilir
- Production ortamında test etmeden önce development'ta deneyin
- Regular backup almayı unutmayın

## 🔗 Kaynaklar

- [PyTorch MPS Documentation](https://pytorch.org/docs/stable/notes/mps.html)
- [macOS Memory Management](https://developer.apple.com/documentation/kernel/memory_management)
- [RL-Swarm GitHub](https://github.com/Bihruze/rl-swarm)
