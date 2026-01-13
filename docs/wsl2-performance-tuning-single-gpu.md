# WSL2 single-GPU performance tuning guide

This guide collects practical tips for getting stable and reasonable throughput from **single-GPU RL-Swarm nodes running inside WSL2 on Windows**.

It is intentionally hardware-agnostic: the checklist should apply to most consumer GPUs
(NVIDIA or AMD). The example rig used when testing these steps was:

- 8-core CPU
- 32 GB RAM
- Single GPU with 20+ GB VRAM (e.g. RX 7900 / 9070-class)
- RL-Swarm running inside Ubuntu on WSL2

The goal is not to micro-benchmark every setting, but to give operators a simple
“sanity checklist” when a node feels slower than expected or becomes unstable.

---

## 1. Understand what “performance” means here

For RL-Swarm, the most visible signal is:

- **examples/s** printed in the logs during training rounds
- how *smoothly* the node joins new rounds without getting stuck or crashing

A few important points:

- examples/s will naturally fluctuate between rounds and stages.
- Network conditions and swarm load also affect how often your node gets work.
- Chasing a few extra percent of throughput is less important than **stability**.

This guide focuses on changes that are low-risk and easy to reproduce.

---

## 2. Windows & WSL2 host settings

These steps live on the Windows side, but strongly affect your WSL2 node.

### 2.1 Power & sleep

On Windows:

- Set the **Power plan** to `High performance` (or the equivalent on your system).
- Disable automatic **sleep / hibernate** while the node is running.
- For laptops, plug in to AC power; battery-saving modes often throttle CPU/GPU.

These avoid the “node silently slows down or disappears overnight” failure mode.

### 2.2 Network stability

Several RL-Swarm components rely on:

- a stable connection to the **Gensyn Testnet**
- the ability to reach **swarm bootstrap peers** (p2p)

Checklist:

- Prefer wired Ethernet over Wi-Fi when possible.
- Avoid frequent VPN hopping; if a VPN is required to reach the testnet, keep it on a
  stable endpoint.
- If you see repeated `failed to connect to bootstrap peers` errors, first suspect
  local firewalls, VPN configuration, or ISP-level blocking.

---

## 3. WSL2 resource allocation

On many machines WSL2 shares resources with other workloads. When the host is busy,
RL-Swarm can become noticeably slower or even unstable.

Practical tips:

- Close unnecessary heavy applications on Windows (other GPU workloads, browsers with
  many tabs, game launchers, etc.).
- Avoid running additional AI training processes inside the same WSL2 instance.
- If you use a custom `.wslconfig`, ensure WSL2 has enough memory and CPUs for the
  node (for example, not restricted to 2 GB RAM on a 32 GB system).

Even without editing `.wslconfig`, simply running the node on a relatively idle host
makes a measurable difference.

---

## 4. Inside Ubuntu: keeping the node lean

From inside your Ubuntu / WSL2 shell, a few simple practices help:

### 4.1 One node per machine

- Run a **single RL-Swarm node** per physical machine unless you know exactly what
  you are doing.
- Multiple nodes contending for the same GPU and network connection usually reduce
  total useful work rather than increase it.

### 4.2 Monitor CPU / memory / GPU usage

Useful tools (choose what you are comfortable with):

- `htop` or `top` for CPU and RAM
- vendor-specific GPU tools (e.g. `nvidia-smi`, `radeontop`) if available
- `watch -n 5 ps aux | grep swarm_launcher` to make sure only the expected
  processes are running

Red flags:

- system constantly swapping (very high RAM usage, high `si/so` in `vmstat`)
- multiple old `swarm_launcher.py` processes left behind after a crash
- GPU fully idle while the node claims to be working

Cleaning up stray processes and restarting the node cleanly often restores normal
behaviour (see also the WSL2 safe restart guide).

---

## 5. Model & logging choices

The default configuration already chooses a relatively small model for many setups.
Still, a few options matter for performance:

- **Model size**: larger models will typically give lower examples/s on the same GPU.
  If you manually override the model, make sure your GPU has enough VRAM and monitor
  for out-of-memory errors.
- **Logging**: running W&B in offline mode (the default in this repo) avoids
  additional network overhead. Syncing logs later is usually sufficient.

When experimenting, change **one variable at a time** and keep notes of its impact
on examples/s and stability.

---

## 6. Handling transient errors without overreacting

In practice you may see occasional warnings or short-lived errors in the logs even on
a healthy node, for example:

- temporary evaluation errors that the system retries
- short network hiccups
- occasional rounds that exit early

Guidelines:

- If the node resumes joining new rounds within a few minutes and examples/s returns
  to its normal range, you usually do **not** need to intervene.
- If the node stops progressing for a long time or repeatedly fails to join rounds,
  consult the connectivity troubleshooting guide and, if needed, perform a clean
  restart.

This avoids manually restarting the node too aggressively when the swarm would have
recovered on its own.

---

## 7. Summary checklist

When a single-GPU WSL2 node feels slow or unstable, a quick checklist:

1. Host is on **High performance** power plan, no automatic sleep.
2. Network is stable; VPN (if used) is not blocking the testnet or bootstrap peers.
3. No heavy competing workloads on Windows or inside WSL2.
4. Only one RL-Swarm node is running on the machine.
5. CPU, RAM and GPU usage look reasonable; no stale `swarm_launcher.py` processes.
6. Model size matches available GPU memory.
7. Transient errors are distinguished from persistent failures before restarting.

These steps were derived from real-world issues on a WSL2 single-GPU setup and are
intended as a living checklist that can be extended as more operators share their
experience.
