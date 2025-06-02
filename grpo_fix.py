# grpo_fix.py
import sys
import os

# Fake GRPO modülü oluştur
class GRPOConfig:
    def __init__(self, *args, **kwargs):
        # PPOConfig'in parametrelerini kullan
        from trl import PPOConfig
        self._ppo_config = PPOConfig(*args, **kwargs)
        # Tüm attribute'ları kopyala
        for attr in dir(self._ppo_config):
            if not attr.startswith('_'):
                setattr(self, attr, getattr(self._ppo_config, attr))

class GRPOTrainer:
    def __init__(self, *args, **kwargs):
        from trl import PPOTrainer
        self._ppo_trainer = PPOTrainer(*args, **kwargs)
        # Tüm method'ları kopyala
        for attr in dir(self._ppo_trainer):
            if not attr.startswith('_'):
                setattr(self, attr, getattr(self._ppo_trainer, attr))

# trl.trainer.grpo_trainer modülünü simüle et
import trl
if not hasattr(trl, 'trainer'):
    trl.trainer = type('trainer', (), {})()
    
trl.trainer.grpo_trainer = type('grpo_trainer', (), {
    'GRPOConfig': GRPOConfig,
    'GRPOTrainer': GRPOTrainer
})()

# Ana trl namespace'ine de ekle
trl.GRPOConfig = GRPOConfig
trl.GRPOTrainer = GRPOTrainer
