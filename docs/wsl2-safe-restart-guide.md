# WSL2 Safe Restart Guide for RL-Swarm

This document explains how to safely stop and restart an RL-Swarm node running inside **WSL2 on Windows**, without leaving orphaned processes or broken p2p sockets.

These steps are based on real scenarios where RL-Swarm froze or terminated unexpectedly and had to be restarted cleanly.


---

## 1. Stop the running RL-Swarm process

If RL-Swarm is running inside a `tmux` session:

Ctrl + B, then D # detach from tmux


List sessions:



tmux ls


Attach back:



tmux attach -t swarm


To stop RL-Swarm cleanly:



Ctrl + C


If it does not stop, force kill:



pkill -f swarm_launcher.py


---

## 2. Stop p2pd (libp2p daemon)

Sometimes p2pd stays alive after RL-Swarm exits.

Check if it is running:


pgrep -f p2pd


If still running:


pkill -f p2pd


---

## 3. Clean stale Unix sockets

WSL2 sometimes leaves behind stale temp sockets:



rm -f /tmp/p2p* /tmp/p2pd.sock


This prevents the error:
> “Address already in use” or “Failed to bind socket”

---

## 4. (Optional) Restart WSL2 cleanly

If networking is broken or the node fails to reconnect:

Close all terminals and run on Windows PowerShell:



wsl --shutdown


Then reopen Ubuntu.

---

## 5. Start RL-Swarm again

Activate the venv:



cd ~/rl-swarm
source .venv/bin/activate


Start p2pd:



p2pd --listen=/tmp/p2pd.sock &


Launch RL-Swarm:



python code_gen_exp/runner/swarm_launcher.py


---

## 6. Verify everything is running

You should see:
- bootstrap peers connected
- rounds progressing
- model loading OK

Optionally check the Telegram bot if you set it up:



/status


---

## Summary

This guide helps WSL2 users safely restart RL-Swarm without leaving broken sessions, orphaned p2p processes, or stale sockets.  
It is based on real issues encountered and resolved during long-runtime node operation.
