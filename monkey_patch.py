import torch
import warnings

# Flash attention yerine normal attention kullan
def use_standard_attention(*args, **kwargs):
    warnings.warn("Flash attention devre dışı, standart attention kullanılıyor")
    return False

# Monkey patch uygula
if hasattr(torch.nn.functional, 'scaled_dot_product_attention'):
    original_sdpa = torch.nn.functional.scaled_dot_product_attention
    
    def patched_sdpa(query, key, value, attn_mask=None, dropout_p=0.0, is_causal=False):
        # Flash attention'ı atlayıp normal implementation kullan
        with torch.backends.cuda.sdp_kernel(
            enable_flash=False, 
            enable_math=True, 
            enable_mem_efficient=True
        ):
            return original_sdpa(query, key, value, attn_mask, dropout_p, is_causal)
    
    torch.nn.functional.scaled_dot_product_attention = patched_sdpa

print("Flash attention devre dışı bırakıldı!")
