import json
import requests
from genrl.logging_utils.global_defs import get_logger
from genrl.blockchain.connections import get_contract, send_via_api, setup_web3
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
                    get_logger().info(f"Registering peer failed with: f{err_name}")
                    raise
                get_logger().info(f"Peer ID [{peer_id}] is already registered! Continuing.")

            except json.JSONDecodeError as decode_err:
                get_logger().warning(
                    "Error decoding JSON during handling of register-peer error"
                )
                raise http_err

    def submit_reward(self, round_num, stage_num, reward, peer_id):
        try:
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
        except requests.exceptions.HTTPError as e:
            raise

    def submit_winners(self, round_num, winners, peer_id):
        try:
            send_via_api(
                self.org_id,
                self.modal_proxy_url,
                "submit-winner",
                {"roundNumber": round_num, "winners": winners, "peerId": peer_id},
            )
        except requests.exceptions.HTTPError as e:
            raise


class PRGCoordinator:
    """
    Coordinator for the PRG game. We don't need contract address or ABI because we rely on the modal proxy app
    to handle routing requests to the correct backend via the endpoints.
    """

    # Note: Parameter names follow the API contract specification
    def __init__(
        self,
        org_id: str,
        modal_proxy_url: str,
    ) -> None:
        self.org_id = org_id
        self.modal_proxy_url = modal_proxy_url

    def bet_token_balance(
        self, peer_id: str
    ) -> int:
        try:
            response = send_via_api(
                self.org_id,
                self.modal_proxy_url,
                "bet-token-balance",
                {
                    "peerId": peer_id,
                },
            )
            if isinstance(response, dict) and "result" in response:
                # The new format returns the actual balance value
                return int(response["result"])
            else:
                get_logger().warning(f"Unexpected response format from bet-token-balance: {response}")
                return 0
        except requests.exceptions.HTTPError as e:
            if e.response is None or e.response.status_code != 500:
                raise

            get_logger().warning("Unknown error calling bet-token-balance endpoint! Continuing.")
            return 0

    def guess_answer(
        self, game_id: int, peer_id: str, clue_id: int, choice_idx: int, bet: int
    ) -> None:
        try:
            send_via_api(
                self.org_id,
                self.modal_proxy_url,
                "guess-answer",
                {
                    "gameId": game_id,
                    "peerId": peer_id,
                    "clueId": clue_id,
                    "choiceIdx": choice_idx,
                    "bet": bet,
                },
            )
        except requests.exceptions.HTTPError as e:
            raise

    def claim_reward(
        self, game_id: int, peer_id: str
    ) -> None:
        try:
            send_via_api(
                self.org_id,
                self.modal_proxy_url,
                "claim-reward",
                {"gameId": game_id, "peerId": peer_id},
            )
        except requests.exceptions.HTTPError as e:
            raise
