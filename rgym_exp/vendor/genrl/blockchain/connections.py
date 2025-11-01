import json
import requests
from eth_account import Account
from web3 import Web3

from rgym_exp.vendor.genrl.logging_utils.global_defs import get_logger

logger = get_logger()


def get_contract(web3: Web3, contract_address: str, abi_path: str):
    with open(abi_path, "r") as f:
        contract_abi = json.load(f)
    if 'abi' not in contract_abi:
        raise ValueError("ABI file must contain an 'abi' field.")
    contract_abi = contract_abi['abi']
    return web3.eth.contract(address=contract_address, abi=contract_abi)  # type: ignore


def send_via_api(org_id, modal_proxy_url, method, args):
    # Construct URL and payload.
    url = modal_proxy_url + method
    payload = {"orgId": org_id} | args

    # Send the POST request.
    response = requests.post(url, json=payload)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()


def setup_web3(url: str) -> Web3:
    # Check testnet connection.
    web3 = Web3(Web3.HTTPProvider(url))
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


def send_chain_txn(web3: Web3, account: Account, txn_factory, chain_id: int):
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
