import json
import logging
from abc import ABC

import requests
from eth_account import Account
from web3 import Web3

ALCHEMY_URL = "https://gensyn-testnet.g.alchemy.com/public"

MAINNET_CHAIN_ID = 685685

SWARM_COORDINATOR_VERSION = "0.2"
SWARM_COORDINATOR_ABI_JSON = (
    f"hivemind_exp/contracts/SwarmCoordinator_{SWARM_COORDINATOR_VERSION}.json"
)
SWARM_COORDINATOR_CONTRACT = "0xcD1351B125b0ae4f023ADA5D09443087a7d99101"

MODAL_PROXY_URL = "http://localhost:3000/api/"

logger = logging.getLogger(__name__)


class SwarmCoordinator(ABC):
    @staticmethod
    def coordinator_contract(web3: Web3):
        with open(SWARM_COORDINATOR_ABI_JSON, "r") as f:
            contract_abi = json.load(f)["abi"]

        return web3.eth.contract(address=SWARM_COORDINATOR_CONTRACT, abi=contract_abi)

    def __init__(self, web3: Web3, **kwargs) -> None:
        self.web3 = web3
        self.contract = SwarmCoordinator.coordinator_contract(web3)
        super().__init__(**kwargs)

    def register_peer(self, peer_id): ...

    def submit_winners(self, round_num, winners): ...

    def update_stage_and_round(self): ...

    def get_bootnodes(self):
        return self.contract.functions.getBootnodes().call()

    def get_round_and_stage(self):
        with self.web3.batch_requests() as batch:
            batch.add(self.contract.functions.currentRound())
            batch.add(self.contract.functions.currentStage())
            round_num, stage_num = batch.execute()

        return round_num, stage_num


class WalletSwarmCoordinator(SwarmCoordinator):
    def __init__(self, private_key: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.account = setup_account(self.web3, private_key)

    def _default_gas(self):
        return {
            "gas": 500000,
            "gasPrice": self.web3.to_wei("50", "gwei"),
        }

    def update_stage_and_round(self):
        send_chain_txn(
            self.web3,
            self.account,
            lambda: self.contract.functions.updateStageAndRound().build_transaction(
                self._default_gas()
            ),
        )

    def register_peer(self, peer_id):
        send_chain_txn(
            self.web3,
            self.account,
            lambda: self.contract.functions.registerPeer(peer_id).build_transaction(
                self._default_gas()
            ),
        )

    def submit_winners(self, round_num, winners):
        send_chain_txn(
            self.web3,
            self.account,
            lambda: self.contract.functions.submitWinners(
                round_num, winners
            ).build_transaction(self._default_gas()),
        )


class ModalSwarmCoordinator(SwarmCoordinator):
    def __init__(self, org_id: str, **kwargs) -> None:
        self.org_id = org_id
        super().__init__(**kwargs)

    def register_peer(self, peer_id):
        try:
            send_via_api(self.org_id, "register-peer", {"peerId": peer_id})
        except requests.exceptions.HTTPError as e:
            if e.response is None or e.response.status_code != 500:
                raise

            # TODO: Verify actual contract errors.
            logger.info(f"Peer ID [{peer_id}] is already registered! Continuing.")

    def submit_winners(self, round_num, winners):
        try:
            send_via_api(
                self.org_id,
                "submit-winner",
                {"roundNumber": round_num, "winners": winners},
            )
        except requests.exceptions.HTTPError as e:
            if e.response is None or e.response.status_code != 500:
                raise

            # TODO: Verify actual contract errors.
            logger.info("Winners already submitted for this round! Continuing.")


def send_via_api(org_id, method, args):
    # Construct URL and payload.
    url = MODAL_PROXY_URL + method
    payload = args | {"orgId": org_id}

    # Send the POST request.
    response = requests.post(url, json=payload)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()


def setup_web3() -> Web3:
    # Check testnet connection.
    web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
    if web3.is_connected():
        logger.info("✅ Connected to Gensyn Testnet")
    else:
        raise Exception("Failed to connect to Gensyn Testnet")
    return web3


def setup_account(web3: Web3, private_key) -> Account:
    # Check wallet balance.
    account = web3.eth.account.from_key(private_key)
    balance = web3.eth.get_balance(account.address)
    eth_balance = web3.from_wei(balance, "ether")
    logger.info(f"💰 Wallet Balance: {eth_balance} ETH")
    return account


def send_chain_txn(
    web3: Web3, account: Account, txn_factory, chain_id=MAINNET_CHAIN_ID
):
    checksummed = Web3.to_checksum_address(account.address)
    txn = txn_factory() | {
        "chainId": chain_id,
        "nonce": web3.eth.get_transaction_count(checksummed),
    }

    # Sign the transaction
    signed_txn = web3.eth.account.sign_transaction(txn, private_key=account.key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    logger.info(f"Sent transaction with hash: {web3.to_hex(tx_hash)}")
