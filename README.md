# RL Swarm

RL Swarm is a fully open source framework for creating RL training swarms over the internet. Running a swarm node allows you to launch a new swarm; alternatively, you can connect to an existing swarm by peering with the public address of one of its constituent nodes.

Each swarm performs RL reasoning as a group, with a gossiping system (using [Hivemind](https://github.com/learning-at-home/hivemind)) for collaborative improvement between models.

RL Swarm is fully open and permissionless, meaning you can run it on a basic consumer laptop at home or on a powerful GPU in the cloud.

Note that this code is experimental - particularly on arm64 architectures.

# Run the swarm

Ensure you that you are using a supported machine/device/environment:

- arm64 CPU with minimum 16gb ram
- CUDA devices (officially supported):
    - RTX 3090
    - RTX 4070
    - RTX 4090
    - A100
    - H100
-  Python >=3.10 (for Mac, you will likely need to upgrade)

## Instructions:

```sh
python3 -m venv .venv
source .venv/bin/activate
./run_rl_swarm.sh
```

If you encounter issues with the coordinator peer, try this backup peer node:

```
DEFAULT_PEER_MULTI_ADDRS="/dns/rl-swarm.gensyn.ai/tcp/38331/p2p/QmQ2gEXoPJg6iMBSUFWGzAabS2VhnzuS782Y637hGjfsRJ" # gensyn coordinator node
```

(Experimental) fix to increase memory on macbook:

```
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
```

## Alternative Instructions:

If you have issues running the above on your development machine or prefer
not to install dependencies locally, we offer a public Docker
image that is ready to run out-of-the-box.
Ensure your Docker engine is configured to allow
adequate space and memory (under System-->Resources) or you might see it being `Killed`. If you don't have a GPU, remove the `--gpus all` flag.

```sh
docker run --gpus all --pull=always -it --rm europe-docker.pkg.dev/gensyn-public-b7d9/public/rl-swarm:v0.0.2 ./run_hivemind_docker.sh
```

## Swarm UI
To launch the Swarm UI, run `docker-compose up --build` and open `0.0.0.0:8080` in your browser.
See the [web/README](./web/README.md) for more details.
