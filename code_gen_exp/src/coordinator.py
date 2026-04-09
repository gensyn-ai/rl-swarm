import json
import requests
from genrl.logging_utils.global_defs import get_logger
from genrl.blockchain.connections import send_via_api
from genrl.blockchain.coordinator import SwarmCoordinator


class ModalSwarmCoordinator(SwarmCoordinator):
    def __init__(
        self,
        web3_url: str,
        contract_address: str,
        org_id: str,
        modal_proxy_url: str,
        swarm_coordinator_abi_json: str,
    ) -> None:
        super().__init__(web3_url, contract_address, swarm_coordinator_abi_json)
        self.org_id = org_id
        self.modal_proxy_url = modal_proxy_url

    def register_peer(self, peer_id):
        try:
            send_via_api(
                self.org_id, self.modal_proxy_url, "register-peer", {"peerId": peer_id}
            )
        except requests.exceptions.HTTPError as http_err:
            if http_err.response is None or http_err.response.status_code != 400:
                raise

            try:
                err_data = http_err.response.json()
                err_name = err_data["error"]
                if err_name != "PeerIdAlreadyRegistered":
                    get_logger().info(f"Registering peer failed with: {err_name}")
                    raise
                get_logger().info(f"Peer ID [{peer_id}] is already registered! Continuing.")

            except json.JSONDecodeError as decode_err:
                get_logger().debug(
                    "Error decoding JSON during handling of register-peer error"
                )
                raise http_err

    def submit_reward(self, round_num, stage_num, reward, peer_id):
        send_via_api(
            self.org_id,
            self.modal_proxy_url,
            "submit-reward",
            {
                "roundNumber": round_num,
                "stageNumber": stage_num,
                "reward": reward,
                "peerId": peer_id,
            },
        )

    def submit_winners(self, round_num, winners, peer_id):
        send_via_api(
            self.org_id,
            self.modal_proxy_url,
            "submit-winner",
            {"roundNumber": round_num, "winners": winners, "peerId": peer_id},
        )
