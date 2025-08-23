# -*- coding: utf-8 -*-
import json
from web3 import Web3
import sys
from datetime import datetime, timezone, timedelta
import time
import requests

# 合约和API配置
ALCHEMY_API_KEY = "HOTVxYyYc0_QPdw3gw10dsJWJfC_QhVE"
ALCHEMY_RPC_URL = f"https://gensyn-testnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
CONTRACT_ADDRESS = Web3.to_checksum_address("0xFaD7C5e93f28257429569B854151A1B8DCD404c2")
ABI_FILE = "abi.json"

# 读取ABI
try:
    with open(ABI_FILE, "r", encoding="utf-8") as f:
        abi = json.load(f)
except Exception as e:
    print(f"无法加载ABI文件: {e}")
    sys.exit(1)

# 获取peerID（命令行参数）
if len(sys.argv) < 2:
    print("用法: python gensyncheck.py <peerID>")
    sys.exit(1)
peer_id = sys.argv[1].strip()
if not peer_id:
    print("peerID不能为空！")
    sys.exit(1)

# 初始化web3和合约
for attempt in range(3):
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))
    if w3.is_connected():
        break
    else:
        print(f"第{attempt+1}次连接Gensyn测试网失败，2秒后重试...")
        time.sleep(2)
else:
    print("无法连接到Gensyn测试网，已重试3次，退出。")
    sys.exit(1)
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

success = False
for attempt in range(3):
    try:
        total_rewards_list = contract.functions.getTotalRewards([peer_id]).call()
        total_rewards = total_rewards_list[0] if total_rewards_list else None
        total_wins = contract.functions.getTotalWins(peer_id).call()
        total_vote = contract.functions.getVoterVoteCount(peer_id).call()
        eoa_list = contract.functions.getEoa([peer_id]).call()
        address = eoa_list[0] if eoa_list else None
        success = True
        break
    except Exception as e:
        print(f"第{attempt+1}次查询失败: {e}")
        time.sleep(2)

if not success:
    print(f"查询失败，已重试3次，跳过本次写入。")
    sys.exit(1)
else:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("="*40)
    print(f"查询时间: {now}")
    print(f"PeerID: {peer_id}")
    print(f"Address: {address if address else '未查到'}")
    print(f"TotalRewards: {total_rewards}")
    print(f"TotalWins: {total_wins}")
    print(f"TotalVote: {total_vote}")

# 查询 address 的最后一笔交易时间

def get_latest_internal_transaction_time(address, api_key):
    url = f"https://gensyn-testnet.explorer.alchemy.com/api?module=account&action=txlistinternal&address={address}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "1" and data.get("result"):
            transactions = data["result"]
            if not transactions:
                return None
            latest_tx = max(transactions, key=lambda x: int(x["timeStamp"]))
            timestamp = int(latest_tx["timeStamp"])
            return datetime.fromtimestamp(timestamp, timezone.utc)
        else:
            return None
    except Exception as e:
        print(f"查询交易时间失败: {e}")
        return None

# 查询 address 的最后一笔交易时间，失败重试3次，3次都失败则仅警告不退出
last_tx_time = None
for attempt in range(3):
    last_tx_time = get_latest_internal_transaction_time(address, ALCHEMY_API_KEY)
    if last_tx_time is not None:
        break
    else:
        print(f"第{attempt+1}次查询交易时间失败，2秒后重试...")
        time.sleep(2)

if last_tx_time:
    now = datetime.now(timezone.utc)
    hours_since = (now - last_tx_time).total_seconds() / 3600
    print(f"最后一笔交易时间: {last_tx_time.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S CST')}")
    print(f"距离现在已过去: {hours_since:.2f} 小时")
    if hours_since > 4:
        print("__NEED_RESTART__")
else:
    print("⚠️ 查询交易时间连续3次失败，跳过本次重启，主流程继续运行。")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              