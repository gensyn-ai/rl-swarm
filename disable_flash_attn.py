import os
import sys

# Flash attention'ı devre dışı bırak
os.environ["DISABLE_FLASH_ATTN"] = "1"
os.environ["USE_FLASH_ATTENTION"] = "0"

# Flash attention import'larını override et
class FakeFlashAttn:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['flash_attn'] = FakeFlashAttn()
sys.modules['flash_attn_2_cuda'] = FakeFlashAttn()
sys.modules['flash_attn.flash_attn_interface'] = FakeFlashAttn()
