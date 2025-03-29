from dataclasses import dataclass
import logging
import sys
import time

import colorlog
from trl import TrlParser
from hivemind_exp.chain_utils import WalletSwarmCoordinator, setup_web3
import schedule


@dataclass
class AdvancerArguments:
    wallet_private_key: str  # EOA wallet private key.
    round_interval_m: float = 30.0


def main():
    # Setup logging.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s:%(name)s:%(message)s",
            log_colors={"INFO": "green", "ERROR": "red"},
        )
    )
    logger.addHandler(handler)

    parser = TrlParser((AdvancerArguments))  # type: ignore
    args: AdvancerArguments = parser.parse_args_and_config()[0]  # type: ignore

    coordinator = WalletSwarmCoordinator(args.wallet_private_key, web3=setup_web3())

    def advance():
        try:
            coordinator.update_stage_and_round()
        except Exception as e:
            logger.error(f"Errored with: {e}. Exiting.")
            sys.exit(1)

        r, s = coordinator.get_round_and_stage()
        logger.info(f"Updated to round {r} and stage {s}.")

    logger.info("Starting round and stage advancer!")
    schedule.every(args.round_interval_m).minutes.do(advance)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
