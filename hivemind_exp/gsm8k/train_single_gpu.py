import sys
import os

# RTX 5090 patch'lerini EN BAŞTA uygula
import transformers.utils
if not hasattr(transformers.utils, 'is_rich_available'):
    transformers.utils.is_rich_available = lambda: False

# vLLM'yi devre dışı bırak
os.environ["USE_VLLM"] = "0"
os.environ["TRL_USE_VLLM"] = "0"
os.environ["DISABLE_VLLM"] = "1"

# xformers'ı devre dışı bırak (RTX 5090 Hopper desteği yok)
os.environ["XFORMERS_DISABLE"] = "1"
os.environ["USE_XFORMERS"] = "0"

# Unsloth'un xformers kullanmasını engelle
import torch
torch.backends.cuda.enable_mem_efficient_sdp(False)
torch.backends.cuda.enable_flash_sdp(False)

# GRPOConfig'i patch'le
from trl import GRPOConfig
original_post_init = GRPOConfig.__post_init__

def patched_post_init(self):
    # generation_batch_size ve steps_per_generation çakışmasını önle
    if hasattr(self, 'generation_batch_size') and hasattr(self, 'steps_per_generation'):
        if self.generation_batch_size is not None and self.steps_per_generation is not None:
            self.generation_batch_size = None
    original_post_init(self)

GRPOConfig.__post_init__ = patched_post_init

import logging
# Needs to be before trl!
from hivemind_exp.runner.grpo_runner import GRPOArguments, GRPORunner
from trl import ModelConfig, TrlParser
from hivemind_exp.chain_utils import (
    ModalSwarmCoordinator,
    WalletSwarmCoordinator,
    setup_web3,
)
from hivemind_exp.gsm8k.generate_prompts import get_stage1_samples as gsm8k_stage1_samples
from hivemind_exp.dapo.generate_prompts import get_stage1_samples as dapo_stage1_samples
from hivemind_exp.debug_utils import print_system_info, TeeHandler, PrintCapture
from hivemind_exp.runner.gensyn.testnet_grpo_runner import (
    TestnetGRPOArguments,
    TestnetGRPORunner,
)

# HivemindGRPOTrainer'ı patch'le
def patch_hivemind_trainer():
    try:
        from hivemind_exp.trainer.hivemind_grpo_trainer import HivemindGRPOTrainer
        
        # PublishingGRPOTrainer sınıfını patch'le
        if hasattr(HivemindGRPOTrainer, 'PublishingGRPOTrainer'):
            original_compute_loss = HivemindGRPOTrainer.PublishingGRPOTrainer.compute_loss
            
            def patched_compute_loss(self, model, inputs, *args, **kwargs):
                # ref_per_token_logps eksikse ekle
                if isinstance(inputs, dict) and "ref_per_token_logps" not in inputs:
                    # Dummy değer ekle veya inputs'tan başka bir değer kullan
                    batch_size = inputs.get("input_ids").shape[0] if "input_ids" in inputs else 1
                    seq_len = inputs.get("input_ids").shape[1] if "input_ids" in inputs else 512
                    inputs["ref_per_token_logps"] = torch.zeros(batch_size, seq_len, device=model.device)
                    print("⚠️ ref_per_token_logps eklendi (dummy değer)")
                
                return original_compute_loss(self, model, inputs, *args, **kwargs)
            
            HivemindGRPOTrainer.PublishingGRPOTrainer.compute_loss = patched_compute_loss
            print("✓ HivemindGRPOTrainer compute_loss patch'i uygulandı")
    except Exception as e:
        print(f"HivemindGRPOTrainer patch uygulanamadı: {e}")

# Patch'i uygula
patch_hivemind_trainer()

# Accelerate DataLoader patch'i
def patch_accelerate_dataloader():
    try:
        from accelerate.data_loader import DataLoaderDispatcher
        original_iter = DataLoaderDispatcher.__iter__
        
        def safe_iter(self):
            try:
                return original_iter(self)
            except UnboundLocalError:
                # Boş iterator döndür
                return iter([])
        
        DataLoaderDispatcher.__iter__ = safe_iter
        print("✓ Accelerate DataLoader patch applied")
    except Exception as e:
        print(f"Failed to patch accelerate: {e}")

# main() fonksiyonundan önce çağır
patch_accelerate_dataloader()

def main():
    # Setup logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Create and add the TeeHandler
    tee_handler = TeeHandler("logs/swarm.log", mode='w')
    tee_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(tee_handler)
    
    # Log system info and set up print capture
    root_logger.debug(print_system_info())
    sys.stdout = PrintCapture(root_logger)
    
    parser = TrlParser((ModelConfig, GRPOArguments, TestnetGRPOArguments, GRPOConfig))  # type: ignore
    model_args, grpo_args, testnet_args, training_args = parser.parse_args_and_config()
    training_args.logging_dir = "logs"
    
    # RTX 5090 için vLLM'yi devre dışı bırak
    training_args.use_vllm = False
    print("✓ vLLM devre dışı bırakıldı (RTX 5090 uyumluluğu için)")
    
    # GRPO config çakışmasını çöz
    if hasattr(training_args, 'generation_batch_size') and hasattr(training_args, 'steps_per_generation'):
        if training_args.generation_batch_size is not None and training_args.steps_per_generation is not None:
            training_args.generation_batch_size = None
            print("✓ generation_batch_size None yapıldı (GRPO config uyumluluğu için)")
    
    # Run main training loop.
    contract_address = testnet_args.contract_address
    if org_id := testnet_args.modal_org_id:
        assert contract_address, "Contract address must be set!"
        runner = TestnetGRPORunner(
            ModalSwarmCoordinator(setup_web3(), contract_address, org_id)
        )
    elif priv_key := testnet_args.wallet_private_key:
        assert contract_address, "Contract address must be set!"
        runner = TestnetGRPORunner(
            WalletSwarmCoordinator(setup_web3(), contract_address, priv_key)
        )
    else:
        runner = GRPORunner()
    
    game = grpo_args.game
    match game:
        case "gsm8k":
            runner.run(model_args, grpo_args, training_args, gsm8k_stage1_samples)
        case "dapo":
            runner.run(model_args, grpo_args, training_args, dapo_stage1_samples)
        case _:
            raise ValueError()

if __name__ == "__main__":
    main()
