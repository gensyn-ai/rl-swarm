import sys
import os
import warnings
import types
from importlib.machinery import ModuleSpec

print("RTX 5090 için tam patch uygulanıyor...")

# 1. Flash Attention Fix
os.environ["FLASH_ATTENTION_SKIP_CUDA_BUILD"] = "TRUE"
os.environ["DISABLE_FLASH_ATTN"] = "1"

class FakeModule:
    def __getattr__(self, name):
        if name == '__spec__':
            return ModuleSpec(self.__class__.__name__, None)
        return FakeModule()
    def __call__(self, *args, **kwargs):
        return self

# Flash attention modüllerini fake ile değiştir
fake_module = FakeModule()
for module_name in ['flash_attn', 'flash_attn_2_cuda', 'flash_attn.flash_attn_interface', 
                    'flash_attn.bert_padding', 'flash_attn.flash_attention', 'flash_attn_cuda']:
    sys.modules[module_name] = fake_module

# 2. vllm'i ZORLA mock'la (kurulu olsa bile)
class MockVLLMModule(types.ModuleType):
    def __init__(self, name):
        super().__init__(name)
        self.__file__ = f"<mock {name}>"
        self.__loader__ = None
        self.__package__ = name if '.' not in name else name.rsplit('.', 1)[0]
        self.__path__ = [f"<mock {name} path>"]
        self.__spec__ = ModuleSpec(name, None)
    
    def __getattr__(self, name):
        child_name = f"{self.__name__}.{name}"
        if child_name in sys.modules and not isinstance(sys.modules[child_name], MockVLLMModule):
            return sys.modules[child_name]
        
        child = MockVLLMModule(child_name)
        setattr(self, name, child)
        sys.modules[child_name] = child
        return child
    
    def __iter__(self):
        return iter([])

# Önce mevcut vllm modüllerini temizle
import sys
vllm_modules_to_remove = [key for key in sys.modules.keys() if key.startswith('vllm')]
for module_name in vllm_modules_to_remove:
    del sys.modules[module_name]

# vllm modül hiyerarşisini oluştur
vllm_modules = [
    'vllm',
    'vllm.__version__',
    'vllm.sampling_params',
    'vllm.adapter_commons',
    'vllm.adapter_commons.request',
    'vllm.distributed',
    'vllm.distributed.utils',
    'vllm.distributed.device_communicators',
    'vllm.distributed.device_communicators.pynccl',
    'vllm.engine',
    'vllm.engine.arg_utils',
    'vllm.config',
    'vllm.model_executor',
    'vllm.model_executor.layers',
    'vllm.model_executor.layers.quantization',
    'vllm.platforms',
    'vllm.utils',
    'vllm._C',
    'vllm._core_C',
    'vllm._core_ext',
    'vllm._custom_ops'
]

for module_name in vllm_modules:
    sys.modules[module_name] = MockVLLMModule(module_name)

# Gerekli sınıfları ekle
sys.modules['vllm'].LLM = type('LLM', (), {'__init__': lambda self, *args, **kwargs: None, 'generate': lambda self, *args, **kwargs: []})
sys.modules['vllm'].SamplingParams = type('SamplingParams', (), {'__init__': lambda self, *args, **kwargs: None})
sys.modules['vllm.sampling_params'].GuidedDecodingParams = type('GuidedDecodingParams', (), {})
sys.modules['vllm.adapter_commons.request'].AdapterRequest = type('AdapterRequest', (), {})
sys.modules['vllm.distributed.utils'].StatelessProcessGroup = type('StatelessProcessGroup', (), {})
sys.modules['vllm.distributed.device_communicators.pynccl'].PyNcclCommunicator = type('PyNcclCommunicator', (), {})
sys.modules['vllm._core_ext'].ScalarType = type('ScalarType', (), {})
sys.modules['vllm.__version__'].__version__ = "0.6.0-mock"

# torch.classes._core_C mock
import torch
if not hasattr(torch, 'classes'):
    torch.classes = types.SimpleNamespace()
if not hasattr(torch.classes, '_core_C'):
    torch.classes._core_C = types.SimpleNamespace()
torch.classes._core_C.ScalarType = type('ScalarType', (), {})

# 3. Transformers patch
import transformers
import transformers.utils

if not hasattr(transformers.utils, 'is_rich_available'):
    transformers.utils.is_rich_available = lambda: False

# 4. CUDA uyarılarını sustur
warnings.filterwarnings("ignore", message=".*CUDA capability sm_120 is not compatible.*")
warnings.filterwarnings("ignore", message=".*xFormers can't load C\\+\\+/CUDA extensions.*")

# 5. PyTorch ayarları
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"

print("✓ Tüm patch'ler uygulandı! (vllm mock kullanılıyor)")
