# Node onboarding checklist (CodeZero)

This checklist is meant to help you verify that your environment is ready
to run an RL Swarm node for the CodeZero environment.

Use it as a quick pre-flight list before you start the swarm or open a
support issue.

---

## 1. Hardware and OS

Before running RL Swarm, make sure that:

- You are on a supported CPU architecture:
  - arm64 or x86.
- You have at least **32 GB RAM** available on the machine.
- You are running a recent Linux or macOS environment, or WSL2 on Windows.

If you are using a GPU:

- Check that your GPU is one of the officially supported CUDA devices
  (for example RTX 3090 / 4090 / 5090, A100, H100).
- Make sure NVIDIA drivers and CUDA are installed and working.

---

## 2. Python and Docker

Required versions:

- Python: `>= 3.10` and `<= 3.13`.
- Docker: a recent Docker Engine installation with the daemon running.

Checklist:

- `python3 --version` prints a supported version.
- `docker --version` runs successfully.
- Docker Desktop (if used) has enough memory assigned for containers.

If `docker-compose` fails, try `docker compose` (without the hyphen), as
described in the README.

---

## 3. Repository and virtual environment

When updating an existing clone of `rl-swarm`, it is important to start from
a fresh virtual environment for CodeZero:

```bash
git pull
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
