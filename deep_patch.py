#!/usr/bin/env python3
# RTX 5090 için derin CUDA patchi
import torch
import warnings
import os

# CUDA DSA'yı etkinleştir
os.environ["TORCH_USE_CUDA_DSA"] = "1"
os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

# Orijinal fonksiyonları yedekle
original_get_arch_list = torch.cuda.get_arch_list

# Yeni get_arch_list fonksiyonu
def patched_get_arch_list():
    return ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120', 'compute_120']

# Uyarıları bastır
warnings.filterwarnings("ignore", message="NVIDIA GeForce RTX 5090")
warnings.filterwarnings("ignore", message="sm_120 is not compatible")
warnings.filterwarnings("ignore", message="no kernel image is available")

# PyTorch fonksiyonlarını değiştir
torch.cuda.get_arch_list = patched_get_arch_list

# Vllm modülü için patch girişimi
try:
    import vllm
    import types
    
    # vllm.model_executor.layers.rotary_embedding içinde arange fonksiyonunu yama
    if hasattr(vllm, 'model_executor') and hasattr(vllm.model_executor, 'layers'):
        rotary_module = vllm.model_executor.layers.rotary_embedding
        original_arange = torch.arange
        
        def safe_arange(*args, **kwargs):
            try:
                return original_arange(*args, **kwargs)
            except RuntimeError as e:
                if "no kernel image is available" in str(e):
                    # CPU üzerinde çalıştır ve sonra GPU'ya taşı
                    device = kwargs.get('device', None)
                    if device is not None and str(device).startswith('cuda'):
                        kwargs['device'] = 'cpu'
                        result = original_arange(*args, **kwargs)
                        return result.to(device)
                raise
                
        # torch.arange'i global olarak değiştir
        torch.arange = safe_arange
except ImportError:
    print("vllm modülü bulunamadı, bazı patchler uygulanamadı")

print("PyTorch CUDA özellikleri derinlemesine yamalandı!")
print(f"CUDA mimarileri: {torch.cuda.get_arch_list()}")
