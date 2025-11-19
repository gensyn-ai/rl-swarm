# WSL2 connectivity & troubleshooting guide

This document summarizes a few connectivity issues that can happen when running RL-Swarm from inside **WSL2 on Windows**, and how they were solved in practice.

The examples below come from a real setup that was successfully fixed and is now running reliably.

---

## 1. `Failed to connect to Gensyn Testnet`

**Error message (simplified):**

```text
Exception: Failed to connect to Gensyn Testnet
hydra.errors.InstantiationException:
Error in call to target 'code_gen_exp.src.coordinator.ModalSwarmCoordinator'

1.1. Root cause

In our case there were two contributing factors:

The web3_url in code_gen_exp/config/code-gen-swarm.yaml was still set to the default:
blockchain:
  alchemy_url: "https://gensyn-testnet.g.alchemy.com/public"

This works only when the public endpoint is reachable and properly configured on Gensyn’s side.

We had not yet switched the config to use our own Alchemy RPC endpoint with an API key.

1.2. How we verified the problem

From inside the WSL2 Ubuntu shell we ran: curl -v "https://gensyn-testnet.g.alchemy.com/public"

The endpoint returned an error such as: {"error": "Unsupported method: / on GENSYN_TESTNET"}
which indicates that we are hitting the server, but not via a proper JSON-RPC endpoint.

1.3. Fix: use a personal Alchemy RPC URL

Log in to Alchemy
 and create a new Gensyn Testnet app.

Copy the HTTPS Node RPC endpoint, which looks like: https://gensyn-testnet.g.alchemy.com/v2/YOUR_ALCHEMY_API_KEY

Open the RL-Swarm config inside WSL2: cd ~/rl-swarm
nano code_gen_exp/config/code-gen-swarm.yaml

Replace the blockchain.alchemy_url value: blockchain:
  alchemy_url: "https://gensyn-testnet.g.alchemy.com/v2/YOUR_ALCHEMY_API_KEY"
Make sure to keep your real key private and never commit it to Git.

Save the file and exit nano.

Test the new endpoint from WSL2: curl "https://gensyn-testnet.g.alchemy.com/v2/YOUR_ALCHEMY_API_KEY" \
  --request POST \
  --header 'content-type: application/json' \
  --data '{"id":1,"jsonrpc":"2.0","method":"eth_blockNumber","params":[]}'

If everything is working, you should get a JSON-RPC response with a hex block number instead of a plain error.

At this point, running ./run_rl_swarm.sh should get past the Failed to connect to Gensyn Testnet error.

2. P2PDaemonError: failed to connect to bootstrap peers

Error message (simplified): hivemind.p2p.p2p_daemon_bindings.utils.P2PDaemonError:
Daemon failed to start: failed to connect to bootstrap peers

2.1. What this usually means

The node can connect to the blockchain (Alchemy), but the peer-to-peer (P2P) layer cannot reach the RL-Swarm bootnodes, for example: /ip4/38.101.215.15/tcp/30021/p2p/...

From the shell we checked: ping -c 4 38.101.215.15
and saw 100% packet loss, which suggests that the route or port is blocked from our current network / IP range.

2.2. Fix: use a VPN that can reach the bootnodes

In our working setup the solution was:

Start a VPN connection (for example to a region where outbound traffic on ports 30021–30023 is allowed).

Re-run RL-Swarm: cd ~/rl-swarm
source .venv/bin/activate
./run_rl_swarm.sh

Once the logs show: ✅ Connected to Gensyn Testnet
...
Joining CodeZero Swarm!

and the rounds start (Starting round: ...), the node is successfully participating in the swarm.

Note: Do not commit your VPN configuration or any private credentials to the repository. The recommendation here is purely about connectivity, not about storing secrets in Git.

3. Verifying that the node is actually running

After fixing both issues above we consistently see logs like: [INFO] ✅ Connected to Gensyn Testnet
[INFO] bootnodes: ['/ip4/38.101.215.15/tcp/30021/p2p/...', ...]
[INFO] ============!!!Joining CodeZero Swarm!!!============
[INFO] 🐝 Hello [your fun swarm name] [PeerID]!
[INFO] Using Model: Qwen/Qwen2.5-Coder-0.5B-Instruct
[INFO] Starting round: 14412/1000000.
Map: 100%|████████...

If the logs keep advancing through rounds and your dashboard shows activity, the node is healthy.

4. Summary

In short:

If you see Failed to connect to Gensyn Testnet
→ double-check blockchain.alchemy_url and switch to a valid Alchemy RPC URL with your own API key.

If you see P2PDaemonError: ... failed to connect to bootstrap peers
→ your network cannot reach the bootnodes; try a VPN or a network where ports 30021–30023 are open.

This guide is based on a real WSL2 setup that is now running RL-Swarm reliably and contributing examples to the Gensyn testnet.
