import torch


DTYPE_MAP = {
    'float16': torch.float16,
    'bfloat16': torch.bfloat16,
    'float32': torch.float32,
    'float64': torch.float64,
    'double': torch.float64, 
    'int8': torch.int8,
    'int16': torch.int16,
    'int32': torch.int32,
    'int64': torch.int64,
    'long': torch.int64, 
    'bool': torch.bool,
}