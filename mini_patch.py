#!/usr/bin/env python3
# RTX 5090 için minimal patch
import torch
import warnings
import os

# CUDA ayarlarını yapılandır
os.environ["TORCH_USE_CUDA_DSA"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# Tüm PyTorch uyarılarını bastır
warnings.filterwarnings("ignore", category=UserWarning)

# Desteklenen mimarileri değiştir
original_get_arch_list = torch.cuda.get_arch_list
torch.cuda.get_arch_list = lambda: ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120', 'compute_120']

# Torch arange fonksiyonunu güvenli hale getir
original_arange = torch.arange

def safe_arange(*args, **kwargs):
    device = kwargs.get('device', None)
    if device is not None and str(device).startswith('cuda'):
        try:
            return original_arange(*args, **kwargs)
        except RuntimeError as e:
            # CUDA hatası durumunda CPU'da hesapla ve GPU'ya taşı
            if "no kernel image is available" in str(e):
                kwargs['device'] = 'cpu'
                result = original_arange(*args, **kwargs)
                return result.to('cuda')
            raise
    return original_arange(*args, **kwargs)

# Arange fonksiyonunu değiştir
torch.arange = safe_arange

print("Minimal PyTorch CUDA patch uygulandı!")
print(f"CUDA mimarileri: {torch.cuda.get_arch_list()}")
