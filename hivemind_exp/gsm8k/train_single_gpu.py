import logging
import hivemind  # Module used for creating the DHT.
import hivemind.p2p.p2p_daemon_bindings.utils as p2p_utils
import colorlog
from trl import GRPOConfig, ModelConfig, TrlParser

from hivemind_exp.chain_utils import (
    ModalSwarmCoordinator,
    WalletSwarmCoordinator,
    setup_web3,
)
from hivemind_exp.gsm8k.generate_prompts import get_stage1_samples
from hivemind_exp.runner.gensyn.testnet_grpo_runner import (
    TestnetGRPOArguments,
    TestnetGRPORunner,
)
from hivemind_exp.runner.grpo_runner import GRPOArguments, GRPORunner

# --- Monkey-patch: Force the await_ready parameter to False during DHT initialization ---
_original_dht_init = hivemind.DHT.__init__

def patched_dht_init(self, *args, **kwargs):
    # Enforce await_ready to be False, bypassing the internal waiting mechanism
    kwargs['await_ready'] = False
    return _original_dht_init(self, *args, **kwargs)

hivemind.DHT.__init__ = patched_dht_init

def main():
    # Setup logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter("%(green)s%(levelname)s:%(name)s:%(message)s")
    )
    root_logger.addHandler(handler)

    parser = TrlParser((ModelConfig, GRPOArguments, TestnetGRPOArguments, GRPOConfig))  # type: ignore
    model_args, grpo_args, testnet_args, training_args = parser.parse_args_and_config()

    # Choose the appropriate runner based on the arguments provided
    if org_id := testnet_args.modal_org_id:
        runner = TestnetGRPORunner(ModalSwarmCoordinator(org_id, web3=setup_web3()))
    elif priv_key := testnet_args.wallet_private_key:
        runner = TestnetGRPORunner(WalletSwarmCoordinator(priv_key, web3=setup_web3()))
    else:
        runner = GRPORunner()

    try:
        # Run the main training loop.
        runner.run(model_args, grpo_args, training_args, get_stage1_samples)
    except p2p_utils.P2PDaemonError as e:
        logging.error("P2P daemon error during runner.run: %s", e)
        # If runner.run fails due to a P2P daemon error

    # Create DHT manually if runner.run() did not successfully setup the DHT:
    try:
        dht = runner.setup_dht(grpo_args)
    except p2p_utils.P2PDaemonError as e:
        logging.error("runner.setup_dht failed: %s. Attempting manual DHT initialization.", e)
        dht = hivemind.DHT(start=True, **runner._dht_kwargs(grpo_args))
    
    # Wait for the DHT to become ready with an extended timeout of 120 seconds
    try:
        dht.wait_until_ready(timeout=120)
    except Exception as e:
        logging.error("DHT wait_until_ready timed out: %s", e)
        return

    logging.info("DHT has been successfully initialized and is ready.")

if __name__ == "__main__":
    main()
