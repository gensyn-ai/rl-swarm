import os
from dataclasses import dataclass
from datetime import datetime
import logging
import hivemind

from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import GRPOConfig, ModelConfig, TrlParser
from huggingface_hub import login

from hivemind_exp.gsm8k.generate_prompts import *
from hivemind_exp.gsm8k.stage_merger import *
from hivemind_exp.trainer.hivemind_grpo_trainer import HivemindGRPOTrainer
from hivemind_exp.utils import HivemindNode

from hivemind_exp.gsm8k.stage_utils import gsm8k_stage_data


########################
# Custom dataclasses
########################
@dataclass
class ScriptArguments:
    #Hugging Face Hub
    hf_token: str | None = None

    # Hivemind arguments
    initial_peer: str | None = None
    public_maddr: str | None = None
    host_maddr: str | None = None
    identity_path: str | None = None
    max_rounds: int = 100

    # Model arguments
    dataset_id_or_path: str = "openai/gsm8k"
    dataset_splits: str = "train"
    tokenizer_name_or_path: str | None = None
    number_of_data_samples: int = 50000
    public_maddr: str | None = None


########################
# Setup logging
########################
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


def get_model(args: GRPOConfig, model_name: str):
    model_init_kwargs = args.model_init_kwargs or {}
    # Disable caching if gradient checkpointing is enabled (not supported)
    model_init_kwargs["use_cache"] = (
        False if args.gradient_checkpointing else model_init_kwargs.get("use_cache")
    )
    return AutoModelForCausalLM.from_pretrained(model_name, **model_init_kwargs)


def get_tokenizer_name(model_args: ModelConfig, script_args: ScriptArguments):
    if script_args.tokenizer_name_or_path:
        return script_args.tokenizer_name_or_path
    if model_args.model_name_or_path:
        return model_args.model_name_or_path
    raise ValueError("unable to resolve tokenizer name")


def grpo_function(
    model_args: ModelConfig,
    script_args: ScriptArguments,
    training_args: GRPOConfig,
):
    #########################
    # Log parameters
    #########################
    logger.info(f"Model parameters {model_args}")
    logger.info(f"Training/evaluation parameters {training_args}")

    batch_size = 2
    training_args.per_device_train_batch_size = batch_size
    training_args.num_generations = batch_size

    ################
    # Load tokenizer
    ################
    tokenizer = AutoTokenizer.from_pretrained(
        get_tokenizer_name(model_args, script_args),
        revision=model_args.model_revision,
        trust_remote_code=model_args.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    #########################
    # Create DHT via Hivemind
    #########################
    dht_kwargs = {}
    initial_peer = script_args.initial_peer
    if initial_peer:
        dht_kwargs["initial_peers"] = [initial_peer]

    if public_maddr := script_args.public_maddr:
        dht_kwargs["announce_maddrs"] = [public_maddr]

    if host_maddr := script_args.host_maddr:
        dht_kwargs["host_maddrs"] = [host_maddr]

    if identity_path := script_args.identity_path:
        dht_kwargs["identity_path"] = identity_path

    dht = hivemind.DHT(start=True, **dht_kwargs)
    if initial_peer:
        print(f"Joining swarm with initial_peer = {initial_peer}")
    else:
        print("Starting swarm at", dht.get_visible_maddrs()[0])

    #####################################
    # Load datasets, prepare, and format
    #####################################
    train_dataset, test_dataset = get_stage1_samples()

    #########################
    # Instantiate DPO trainer
    #########################

    assert model_args.model_name_or_path
    model = get_model(training_args, model_args.model_name_or_path)

    if initial_peer:
        node = HivemindNode(model_args.model_name_or_path)
    else:
        node = HivemindNode.coordinator(model_args.model_name_or_path)

    stage_data = gsm8k_stage_data(dht, node, train_dataset, test_dataset)
    stage_data.max_rounds = script_args.max_rounds
    trainer = HivemindGRPOTrainer(
        dht=dht,
        node=node,
        model=model,
        tokenizer=tokenizer,
        config=training_args,
        stage_data=stage_data,
    )

    ###############
    # Training loop
    ###############

    # Train the model
    logger.info(
        f"*** Starting training {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for {training_args.num_train_epochs} epochs***"
    )
    trainer.train()

    logger.info("*** Training complete! ***")


def main():
    parser = TrlParser((ModelConfig, ScriptArguments, GRPOConfig))
    model_args, script_args, training_args = parser.parse_args_and_config()

    # Log into hf hub if specified in configs and needed info is provided
    if (script_args.hf_token not in [None, "None"]):
        training_args.push_to_hub_token = script_args.hf_token
        login(token=training_args.push_to_hub_token, add_to_git_credential=True)
    else:
        training_args.push_to_hub_token = None

    # Run the main training loop
    grpo_function(model_args, script_args, training_args)


if __name__ == "__main__":
    main()
