import sys
import os
import warnings

# Flash attention'ı tamamen devre dışı bırak
os.environ["FLASH_ATTENTION_SKIP_CUDA_BUILD"] = "TRUE"
os.environ["DISABLE_FLASH_ATTN"] = "1"

# Fake flash_attn modülleri oluştur
class FakeModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None
    
    def __call__(self, *args, **kwargs):
        return None

# Tüm flash_attn modüllerini fake modüllerle değiştir
fake_module = FakeModule()
sys.modules['flash_attn'] = fake_module
sys.modules['flash_attn_2_cuda'] = fake_module
sys.modules['flash_attn.flash_attn_interface'] = fake_module
sys.modules['flash_attn.bert_padding'] = fake_module
sys.modules['flash_attn.flash_attention'] = fake_module
sys.modules['flash_attn_cuda'] = fake_module

# Transformers'ın flash attention kontrolünü override et
import transformers
if hasattr(transformers, '_is_flash_attn_available'):
    transformers._is_flash_attn_available = lambda: False
if hasattr(transformers, '_is_flash_attn_2_available'):
    transformers._is_flash_attn_2_available = lambda: False

# Import sırasında hata vermesin diye bazı fake değerler
fake_module.flash_attn_func = lambda *args, **kwargs: args[0]
fake_module.flash_attn_varlen_func = lambda *args, **kwargs: args[0]
fake_module.index_first_axis = lambda *args, **kwargs: args[0]
fake_module.pad_input = lambda *args, **kwargs: (args[0], None, None)
fake_module.unpad_input = lambda *args, **kwargs: (args[0], None)

print("Flash attention tamamen devre dışı bırakıldı!")
