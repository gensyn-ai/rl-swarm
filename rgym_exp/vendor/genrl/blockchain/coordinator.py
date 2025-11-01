from abc import ABC
from web3 import Web3

from rgym_exp.vendor.genrl.blockchain.connections import (
    setup_web3,
    get_contract
)
from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger

logger = get_logger()


class SwarmCoordinator(ABC):
    def __init__(self, web3_url: str, contract_address: str, swarm_coordinator_abi_json: str, **kwargs) -> None:
        self.web3 = setup_web3(web3_url)
        self.contract = get_contract(self.web3, contract_address, swarm_coordinator_abi_json)
        super().__init__(**kwargs)

    def register_peer(self, peer_id): ...

    def submit_winners(self, round_num, winners, peer_id): ...

    def submit_reward(self, round_num, stage_num, reward, peer_id): ...

    def get_bootnodes(self):
        return self.contract.functions.getBootnodes().call()

    def get_round_and_stage(self):
        with self.web3.batch_requests() as batch:
            batch.add(self.contract.functions.currentRound())
            batch.add(self.contract.functions.currentStage())
            round_num, stage_num = batch.execute()

        return round_num, stage_num
