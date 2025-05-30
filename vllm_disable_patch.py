import os

# vLLM kullanımını devre dışı bırak
os.environ["USE_VLLM"] = "0"
os.environ["TRL_USE_VLLM"] = "0"
os.environ["DISABLE_VLLM"] = "1"

# GRPOConfig'i patch'le
try:
    from trl import GRPOConfig
    original_init = GRPOConfig.__init__
    
    def patched_init(self, *args, **kwargs):
        # use_vllm parametresini zorla False yap
        kwargs['use_vllm'] = False
        original_init(self, *args, **kwargs)
        self.use_vllm = False
    
    GRPOConfig.__init__ = patched_init
    print("✓ vLLM devre dışı bırakıldı")
except Exception as e:
    print(f"GRPOConfig patch uygulanamadı: {e}")
