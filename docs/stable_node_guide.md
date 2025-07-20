# Stable Setup of RL‑Swarm Node on WSL (Ubuntu) with RAM Limit & SWAP

This guide shows how to run your RL‑Swarm node **locally** on Windows using **WSL2 + Ubuntu 22.04**, including memory limiting and swap configuration for stability.

---

## ✅ Environment

- Windows 10 or 11  
- WSL2 (Windows Subsystem for Linux)  
- Ubuntu 22.04 (installed from Microsoft Store)  
- Limited RAM use and SWAP enabled  
- Installation using only official commands

---

## 🔧 WSL Configuration: Limit RAM & Enable SWAP

Create or edit the file:  
`C:\Users\<YourUsername>\.wslconfig`

Insert the following:

```
[wsl2]
memory=6GB
processors=4
swap=16GB
localhostForwarding=true
```

Save the file, then run in PowerShell or Command Prompt:

```powershell
wsl --shutdown
```

---

## 🐧 Install Ubuntu (if not installed yet)

1. Open **Microsoft Store**  
2. Search for **Ubuntu 22.04 LTS** and install  
3. Launch **Ubuntu** from Start menu  
4. Create your WSL username and password

---

## 🚀 Install and Run RL‑Swarm (official steps only)

Open Ubuntu (WSL) terminal and run:

```bash
cd ~
rm -rf rl-swarm
git clone https://github.com/gensyn-ai/rl-swarm.git
cd rl-swarm
python3 -m venv venv
sudo apt update
sudo apt install -y python3 python3-pip
pip install pycosat
tmux new -s swarm
./run_rl_swarm.sh
```

> ℹ️ To detach from `tmux` without stopping the node, press:
> `Ctrl + B` then `D`  
> To reattach:  
> `tmux attach -t swarm`

---

## 🔄 Optional: Create Swap File Manually in Ubuntu

If swap isn't created by `.wslconfig`, run:

```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

To make swap permanent:

```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Check swap with:

```bash
free -h
```

---

## 🧪 Verify Node Operation

- Run `htop` to monitor RAM/SWAP usage  
- Confirm that port `3000` is active (inside `tmux`)  
- Access via browser (use SSH tunnel if necessary)

---

## 🔍 Summary of Testing

- VPS (Time4VPS): encountered instability after a few hours  
- Local WSL with 6GB RAM + 16GB SWAP: stable 24+ hours  
- All setup steps use only official commands  
- Running inside `tmux` ensures node stays active during terminal disconnects

---

## 💬 Feedback & Contributions

Found this helpful? Feel free to share it in Discord or open another Pull Request to improve it further.

**Contributed by**: Viktorino 🇺🇦

