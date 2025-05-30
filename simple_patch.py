#!/usr/bin/env python3
# RTX 5090 için basit ve doğrudan patch
import torch
import warnings
import os

# CUDA DSA'yı etkinleştir
os.environ["TORCH_USE_CUDA_DSA"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# Patching işlemleri
# 1. PyTorch'un uyarı fonksiyonunu sessizleştir
original_warn_func = torch.cuda.__init__._warn_on_cuda_device_unsupported = lambda *args, **kwargs: None

# 2. Arange fonksiyonunu güvenli hale getir
original_arange = torch.arange

def safe_arange(*args, **kwargs):
    device = kwargs.get('device', None)
    if device is not None and str(device).startswith('cuda'):
        try:
            return original_arange(*args, **kwargs)
        except RuntimeError as e:
            if "no kernel image is available" in str(e):
                kwargs['device'] = 'cpu'
                result = original_arange(*args, **kwargs)
                return result.to(device)
            raise
    return original_arange(*args, **kwargs)

torch.arange = safe_arange

# 3. Get_arch_list fonksiyonunu patch et
original_get_arch_list = torch.cuda.get_arch_list

def patched_get_arch_list():
    return ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120', 'compute_120']

torch.cuda.get_arch_list = patched_get_arch_list

# Uyarıları bastır (tüm kaynaklardan)
warnings.filterwarnings("ignore", category=UserWarning)

print("PyTorch CUDA basit patch uygulandı!")
print(f"CUDA mimarileri: {torch.cuda.get_arch_list()}")
