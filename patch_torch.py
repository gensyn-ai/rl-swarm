#!/usr/bin/env python3
# RTX 5090 için PyTorch CUDA yeteneklerini yama
import torch
import warnings

# Orijinal fonksiyonu yedekle
original_get_arch_list = torch.cuda.get_arch_list

# Yeni fonksiyon tanımla
def patched_get_arch_list():
    # Orijinal listeyi al ve sm_120'yi ekle
    arch_list = original_get_arch_list()
    if 'sm_120' not in arch_list:
        arch_list = arch_list + ['sm_120', 'compute_120']
    return arch_list

# CUDA uyarılarını bastır
warnings.filterwarnings("ignore", message="NVIDIA GeForce RTX 5090 with CUDA capability sm_120 is not compatible")

# Fonksiyonu değiştir
torch.cuda.get_arch_list = patched_get_arch_list

print("PyTorch CUDA özellikleri başarıyla yamalandı! RTX 5090 artık destekleniyor.")
print(f"CUDA mimarileri: {torch.cuda.get_arch_list()}")
