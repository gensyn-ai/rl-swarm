If you are stuck on the login screen of the Gensyn testnet, follow the commands below:
`pkill -f "SCREEN.*gensyn"`
`screen -S gensyn`
`cd rl-swarm`
`curl -o modal-login/app/page.tsx https://raw.githubusercontent.com/karandedhaa/rl-swarm/main/modal-login/app/page.tsx`
`python3 -m venv .venv && . .venv/bin/activate && ./run_rl_swarm.sh`
