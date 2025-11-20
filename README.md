# RL Swarm

RL Swarm is a peer-to-peer system for reinforcement learning. It allows you to train models collaboratively with others in the swarm, leveraging their collective intelligence. It is open source and permissionless, meaning you can run it on a consumer laptop at home or on a powerful GPU in the cloud. You can also connect your model to the Gensyn Testnet to receive an on-chain identity that tracks your progress over time.

> **Update -> CodeZero Swarm Environment**  
> RL Swarm now powers **CodeZero**, the newest active environment on the Gensyn Testnet.  
> CodeZero extends RL Swarm beyond reasoning and math into **coding tasks**, where models take on distinct roles, *Solvers*, *Proposers*, and *Evaluators*, to enable **collaborative learning** across a decentralized network.

Models (CodeZero):
   - **Qwen2.5-Coder-0.5B-Instruct** — Solver role  
   - **Qwen2.5-Coder-1.5B-Instruct** — Evaluator (frozen)  

Currently, we are running **CodeZero** on the Gensyn Testnet.  

CodeZero replaces the previous *reasoning-gym* environment, introducing a new task domain focused on programming challenges and model-based evaluation.  

If you previously ran RL Swarm during the reasoning-gym phase, your node will automatically transition to CodeZero after you update using the steps below:

**If you are using Docker:**
- Simply run `git pull` and restart your swarm. Docker will handle the environment updates automatically.

**If you are using the `run_rl_swarm.sh` script:**
- You must remove your old Python virtual environment and create a fresh one after updating. Run the following commands in your RL Swarm directory:

```sh
git pull
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
```

This will ensure your environment is clean and compatible with CodeZero.

This iteration of rl-swarm is powered by the [GenRL](https://github.com/gensyn-ai/genrl) library.  It is a fully composable framework for decentralized reinforcement learning which enables users to create and customize their own swarms for reinforcement learning with multi-agent multi-stage environments.

The **CodeZero** environment runs on the same RL Swarm + GenRL stack, extending the framework to cooperative code generation and debugging tasks. 

> **Note:** As of the CodeZero release, all RL Swarm nodes train on code-generation tasks rather than reasoning-gym problems. The setup process remains identical.

## Requirements

Your hardware requirements will vary depending on a number of factors including model size and the accelerator platform you use.  Users running a large NVIDIA GPU will be assigned a model from the large model pool, while users running less powerful hardware will be assigned a model from the small model pool. This design decision is intended to allow users to advance at a similar rate regardless of the hardware they use, maximizing their utility to the swarm.      

**Supported Hardware**

- arm64 or x86 CPU with a minimum of 32GB RAM (note that if you run other applications during training it might crash the training).

OR

- CUDA devices (officially supported):
    - RTX 3090
    - RTX 4090
    - RTX 5090
    - A100
    - H100

With either configuration, you will need Python >=3.10,<=3.13 (for Mac, you will likely need to upgrade).

## **Please read before continuing!**

This software is **experimental** and provided as-is for users who are interested in using (or helping to develop) an early version of the Gensyn Protocol for training models.

If you care about on-chain participation, you **must** read the [Identity Management](#identity-management) section below.

If you encounter issues, please first check [Troubleshooting](#troubleshooting). If you cannot find a solution there, please check if there is an open (or closed) [Issue](../../issues). If there is no relevant issue, please file one and include 1) all relevant [logs](#troubleshooting), 2) information about your device (e.g. which GPU, if relevant), and 3) your operating system information.

### ⚠️ CodeZero Release - Important Update Required ⚠️

**Once CodeZero is released, you must update your RL Swarm installation to continue earning participation points.**

With the CodeZero release, you must update your RL Swarm installation to transition to the new environment. All of your previous participation and leaderboard activity will be preserved and carried forward.

Once you update, any new node you launch will automatically participate in CodeZero and continue accruing activity points for the leaderboard as before.

Existing nodes running the previous "reasoning-gym" Swarm can continue operating without issue, but **will not accrue additional tracked participation points on the leaderboard after the CodeZero launch unless you update**.

> Make sure to update to continue earning activity points!

**To update:**

- **If you are using Docker:** Simply run `git pull` and restart your swarm. 

- **If you are using the `run_rl_swarm.sh` script:** You must remove your old virtual environment and create a fresh one:
  ```sh
  git pull
  rm -rf .venv
  python -m venv .venv
  source .venv/bin/activate
  ```

Then restart your swarm.

## Instructions

### Run the Swarm

The easiest way to run RL Swarm is using Docker. This ensures a consistent setup across all operating systems with minimal dependencies.

#### 1. Clone this repo

```sh
git clone https://github.com/gensyn-ai/rl-swarm
```

**Existing RL Swarm users need to delete their old virtual environment and create a new one after pulling the latest changes:**

```sh
git pull
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
```

#### 2. Install Docker

Make sure you have Docker installed and the Docker daemon is running on your machine. 

To do that, follow [these instructions](https://docs.docker.com/get-started/get-docker/) according to your OS. Ensure you allot sufficient memory to the Docker containers. For example, if you are using Docker Desktop, this can be done by going to Docker Desktop Settings > Resources > Advanced > Memory Limit, and increasing it to the maximum possible value.

#### 3. Start the Swarm

Run the following commands from the root of the repository.

> Once updated, your node will automatically participate in **CodeZero**, the active swarm environment focused on collaborative coding.

##### CPU support

 If you’re using a Mac or if your machine has CPU-only support:
```sh
docker-compose run --rm --build -Pit swarm-cpu
```

##### GPU support

If you're using a machine with an officially supported GPU:
```sh
docker-compose run --rm --build -Pit swarm-gpu
```

##### Docker compose issue

If `docker-compose` does not work when running the above commands, please try `docker compose` (no hyphen) instead. I.e. ` docker compose run --rm --build -Pit swarm-gpu`. This issue sometimes occurs on users running Ubuntu.

### Experimental (advanced) mode

If you want to experiment with the [GenRL](https://github.com/gensyn-ai/genrl) library or the [configurable parameters](https://github.com/gensyn-ai/rl-swarm/blob/main/rgym_exp/config/rg-swarm.yaml ), we recommend you run RL Swarm via shell script:

```sh
python3 -m venv .venv
source .venv/bin/activate
./run_rl_swarm.sh
```  
To learn more about experimental mode, check out our [getting started guide](https://github.com/gensyn-ai/genrl/blob/main/getting_started.ipynb).


### Login

1. A browser window will pop open (you'll need to manually navigate to http://localhost:3000/ if you're on a VM).
2. Click 'login'.
3. Log in with your preferred method.

### Huggingface

If you would like to upload your model to Hugging Face, enter your Hugging Face access token when prompted. You can generate one from your Hugging Face account, under [Access Tokens](https://huggingface.co/docs/hub/en/security-tokens).

### AI Prediction Market

During setup, you'll be asked if you'd like to participate in the **AI Prediction Market**.

This is an experiment we're running in which:
- RL Swarm models join the market and place bets on which answer to a reasoning problem they believe is correct. 
- Evidence is revealed step by step throughout the game. Models can update their beliefs by placing new bets as information arrives.
- Correct bets placed earlier pay out more than those made later, rewarding models that identify the right answer quickly and confidently.
- The Judge evaluates the final evidence and issues a decision, determining which bets succeed. 

You'll be entered into the prediction market by default, by pressing `ENTER` or answering `Y` to the Prediction Market prompt. If you'd like to opt out, just answer `N`.
To learn more, head to our [blog](https://blog.gensyn.ai/) and check out our [Gensyn Testnet Dashboard](https://dashboard.gensyn.ai/).

### Initial peering and training

From this stage onward your device will begin training. You should see your peer register and vote on-chain [here](https://gensyn-testnet.explorer.alchemy.com/address/0x7745a8FE4b8D2D2c3BB103F8dCae822746F35Da0?tab=logs).

You can also track your training progress in real time:
- On the Gensyn Testnet Dashboard: [dashboard.gensyn.ai](https://dashboard.gensyn.ai)

## Environment Overview (CodeZero)

CodeZero extends RL Swarm with distinct node roles that collaborate on programming challenges:

| Role        | Description                                                              |
|-------------|--------------------------------------------------------------------------|
| **Solver**  | Learns locally on code tasks using GRPO; shares rollouts with peers      |
| **Proposer**| Generates coding problems and adjusts difficulty heuristically           |
| **Evaluator**| Frozen model predicting correctness and assigning rewards               |

Users will run **Solver** nodes.

### Updating RL Swarm

**If you are using Docker:**
- Simply run `git pull` and restart your swarm. You may also need to rebuild your containers:
  ```sh
  git pull
  docker-compose build
  ```

**If you are using the `run_rl_swarm.sh` script:**
- You must remove your old virtual environment and create a new one:
  ```sh
  git pull
  rm -rf .venv
  python -m venv .venv
  source .venv/bin/activate
  ```

After pulling the latest changes, restart your swarm following the [instructions above](#run-the-swarm). This ensures you have the latest features, bug fixes, and compatibility updates.

**Note**: If you're using Docker, you may need to rebuild your containers after updating:
```sh
docker-compose build
```

## Identity management

> CodeZero uses the same identity and peer registration system as previous RL Swarm environments. No new setup is required.

### Introduction

On-chain identity is managed via an Alchemy modal sign-in screen. You need to supply an email address or login via a supported method (e.g. Google). This creates an EOA public/private keys (which are stored by Alchemy). You will also receive local session keys in the `userApiKey`. Note that these aren't your EOA public/private keys. 

During the initial setup process, you will also create a `swarm.pem` file which maintains the identity of your peer. This is then registered on chain using the EOA wallet hosted in Alchemy, triggered using your local api keys. This links the `swarm.pem` to the `email address` (and corresponding EOA in Alchemy).

**If you want to link multiple nodes to a single EOA**, simply sign up each node using the same email address. You will get a new peer ID for each node, however they will all be linked to the same EOA that your email is linked to.

**Please note**: if you are using a fork of this repo, or a service organised by someone else (e.g. a 'one click deployment' provider) the identity management flow below is not guaranteed.

### What this means
In the following two scenarios, everything will work (i.e. you will have an on-chain identity linked with your RL Swarm peer training):

- The very first time you run the node from scratch with a new email address. The smart account will be created fresh and linked with the swarm.pem that is also fresh.
- If you run it again with a `swarm.pem` AND login the original `email address` used with that `swarm.pem`. Note: this will throw an error into the log on registration but will still be able to sign transactions.

In the following two scenarios, it will not work (i.e. you won't have an on-chain identity linked with your RL Swarm peer training):

- If you keep your `swarm.pem` and try to link it to an `email address` distinct from the one with which it was first registered.

Therefore, you should do these actions in the following scenarios

- **Signed up with `email address`, generated `swarm.pem`, BUT lost `swarm.pem`** OR **You want to run multiple nodes at once**: run from scratch with the same email address and generate a new `swarm.pem`. 
- **Signed up with `email address`, generated `swarm.pem`, kept `swarm.pem`** -> you can re-run a single node using this pair if you've still got them both.

## Troubleshooting

- **How do I find my logs?** You can find them inside the `/logs` directory:
    - `yarn.log`: This file contains logs for the modal login server.
    - `swarm.log`: This is the main log file for the RL Swarm application.
    - `wandb/`: This directory contains various logs related to your training runs, including a `debug.log` file. These can be updated to Weights & Biases (only available if you log_with wandb).

- **My peer 'skipped a round'**: this occurs when your device isn't fast enough to keep up with the pace of the swarm. For example, if you start training at round 100 and by the time you finish training the rest of the swarm reaches round 102, you will skip round 101 and go straight to 102. This is because your peer is more valuable if it is participating in the active round.
- **My model doesn't seem to be training?**

    - If you're using a consumer device (e.g. a MacBook), it is likely just running slowly - check back in 20 minutes.

- **Logging in with a new account after previous login?**
    
    - Make sure you click 'Logout' on the login screen before you leave your previous session
    - Make sure you delete `swarm.pem` from the root directory (try `sudo rm swarm.pem`). If you don't do this, and you previously registered with the peer-id stored in this file, it will disrupt the training process.

- **Issues with the Login screen**

    - **Upgrade viem**: some users report issues with the `viem` package. There are two fixes:
        - in the `modal-login/package.json` update: `"viem": "2.25.0"`
        - in the terminal `cd /root/rl-swarm/modal-login/ && yarn upgrade && yarn add next@latest && yarn add viem@latest`

- **I'm getting lots of warnings**
    - This is expected behaviour and usually the output of the package managers or other dependencies. The most common is the below Protobuf warning - which can be ignored
        ```
        WARNING: The candidate selected for download or install is a yanked version: 'protobuf' candidate...
        ```

- **Issues on VMs/VPSs?**

    - **How do I access the login screen if I'm running in a VM?**: port forwarding. Add this SSH flag: `-L 3000:localhost:3000` when connecting to your VM. E.g. `gcloud compute ssh --zone "us-central1-a" [your-vm] --project [your-project] -- -L 3000:localhost:3000`. Note, some VPSs may not work with `rl-swarm`. Check the Gensyn [discord](https://discord.gg/AdnyWNzXh5) for up-to-date information on this.
    
    - **Disconnection/general issues**: If you are tunneling to a VM and suffer a broken pipe, you will likely encounter OOM errors or unexpected behaviour the first time you relaunch the script. If you `control + c` and kill the script it should spin down all background processes. Restart the script and everything should function normally.

- **Issues with npm/general installation?**

    - Try  `npm install -g node@latest`

- **OOM errors on MacBook?**
    - Try this (experimental) fix to increase memory:
        ```
        export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
        ```
- **I have a Windows machine, can I still train a model on the swarm?**: Yes - but this is not very well tested and may require you to do some debugging to get it set up properly. Install WSL and Linux on your Windows machine using the following instructions: https://learn.microsoft.com/en-us/windows/wsl/install

- **I want to move my to a different machine and/or restart with a fresh build of the repo, but I want my animal name/peer id to persist.**: To achieve this simply backup the `swarm.pem` file on your current machine and then put it in the corresponding location on your new machine/build of the repo.

- **I have multiple GPUs on one machine, can I run multiple peers?**: Yes - but you'll need to manually change things. You'll need to isolate each GPU, install this repo for each GPU, and expose each peer under a different port to pass the modal onboard.

- **My round/stage is behind the smart contract/other peers?**: This is expected behaviour given the different speeds of machines in the network. Once your machine completes its current round, it will move to the current round.

- **I want to use a bigger and/or different model in the RL swarm, can I do that?**: Yes - but we only recommend doing so if you are comfortable understanding what size model can reasonably run on your hardware.  If you elect to bring a custom model, just paste the repo/model name into the command line when prompted.

- **I am running a model in the swarm on my CPU, have received a python `RuntimeError`, and my training progress seems to have stopped.**: There are several possible causes for this, but before trying anything please wait long enough to be sure your training actually is frozen and not just slow (e.g., wait longer than a single training iteration has previously taken on your machine). If you're sure training is actually frozen, then some things to try are:
    - Set this (experimental) fix: `export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 && ./run_rl_swarm.sh`

- **I am running a node but I'm not seeing any Prediction Market bets on the dashboard**: 
    - Make sure you answered `Y` to the AI Prediction Market prompt (see [above](#ai-prediction-market)).
    - Log in to the [Gensyn Testnet Dashboard](https://dashboard.gensyn.ai/) and check the `Your Bets` section under the `Judge` tab to confirm whether any bets have been placed by your node.
    - Review the following log files for errors or additional information: `logs/prg_record.txt` and `logs/swarm_launcher.log`.

---

### Learn More

- [Dashboard](https://dashboard.gensyn.ai/)
- [Docs](https://docs.gensyn.ai/testnet/rl-swarm)
