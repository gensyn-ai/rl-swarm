If you're getting failed to connect to bootstrap peers, follow the commands below:
step-1:
```bash
pkill -f "SCREEN.*gensyn"
```
step2:
```bash
screen -S gensyn
```
step-3:
```bash
cd rl-swarm
```
step-4:
```bash
curl -o hivemind_exp/runner/gensyn/testnet_grpo_runner.py https://raw.githubusercontent.com/karandedhaa/rl-swarm/main/hivemind_exp/runner/gensyn/testnet_grpo_runner.py
```
step-5:
![image](https://github.com/user-attachments/assets/05cebb9d-3e30-41be-90d3-c3fc17dfc4eb)
Now check the above screenshot and check the ip in my case it's ending with 14, if yours also same then skip this step.
```bash
nano hivemind_exp/runner/gensyn/testnet_grpo_runner.py
```
scroll down and change ip in the code with your respective ip(like the one in the first screenshot), then press ctrl+x y enter
![image](https://github.com/user-attachments/assets/62200c45-abd7-4102-972f-fc7bee809b85)
step-6:
```bash
python3 -m venv .venv && . .venv/bin/activate && PEER_MULTI_ADDRS="" ./run_rl_swarm.sh
```
