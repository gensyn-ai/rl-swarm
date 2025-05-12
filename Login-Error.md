If you are stuck on the login screen of the Gensyn testnet, follow the commands below:
```bash
pkill -f "SCREEN.*gensyn"
```
You can replace you screen name in the above command
```bash
screen -S gensyn
```
```bash
cd rl-swarm
```
```bash
curl -o modal-login/app/page.tsx https://raw.githubusercontent.com/karandedhaa/rl-swarm/main/modal-login/app/page.tsx
```
```bash
python3 -m venv .venv && . .venv/bin/activate && ./run_rl_swarm.sh
```
