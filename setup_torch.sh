#!/bin/bash
# PyTorch 2.7.0 kurulumu
pip uninstall -y torch torchvision torchaudio
pip install torch==2.7.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Sürümü kontrol et
python -c "import torch; print(f'PyTorch sürümü: {torch.__version__}'); print(f'CUDA kullanılabilir: {torch.cuda.is_available()}'); print(f'Desteklenen CUDA özellikleri: {torch.cuda.get_arch_list()}')"
